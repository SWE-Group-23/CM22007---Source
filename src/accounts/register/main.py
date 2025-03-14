"""
Handles the multi-stage registration process.
"""

import os
import json
import logging
import re

import valkey
import argon2
import pyotp
from cassandra.cqlengine import query

import shared
from shared import rpcs
from shared.models import accounts as model


class RegisterRPCServer(rpcs.RPCServer):
    """
    Serves the register RPC.
    """

    def __init__(self, valkey, rabbitmq_user, rabbitmq_pass, rpc_prefix):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)
        self.vk = valkey
        self.ph = argon2.PasswordHasher()

    def _check_username(self, username: str) -> bool:
        """
        Checks if a username is formatted
        correctly:
            - must be 5 chars or longer
            - must only contain:
                [0-9A-Za-z-_.]
            - cannot begin or end with special chars
        """
        if len(username) < 5:
            return False

        # can't begin with special characters -_.
        # must only consist of alphanumeric and -_.
        # can't end with special characters -_.
        pattern = re.compile(
            r"^[A-Za-z0-9](?:[A-Za-z0-9\-._]{0,}[A-Za-z0-9])?$")

        if not pattern.match(username):
            return False

        return True

    def _check_valid_username(self, req: dict) -> str:
        """
        Checks if a username already exists
        or is formatted correctly
        and creates a JSON response based
        on if it does.
        """
        # check username is in valid format
        if not self._check_username(req["data"]["username"]):
            return rpcs.response(200, {"valid": False})

        try:
            model.Accounts.get(username=req["data"]["username"])

            # account found as DoesNotExist not thrown
            return rpcs.response(200, {"valid": False})

        # couldn't get user with username
        except query.DoesNotExist:
            # set authUser (should be a session token)
            # register stage in valkey
            stage = {"stage": "username-valid",
                     "username": req["data"]["username"]}

            self.vk.setex(
                f"register:{req['authUser']}", 60 * 30, json.dumps(stage))

            return rpcs.response(200, {"valid": True})

    def _set_password(self, req: dict) -> str:
        # get current user state from valkey
        cur_stage_raw = self.vk.get(f"register:{req['authUser']}")

        # token either timed out or didn't exist
        if cur_stage_raw is None:
            return rpcs.response(400, {"reason": "Token doesn't exist."})

        # check token at correct stage
        cur_stage = json.loads(cur_stage_raw)
        if cur_stage["stage"] != "username-valid":
            return rpcs.response(403, {"reason": "Token not at correct step."})

        # hash+salt password with argon2
        hash = self.ph.hash(req["data"]["password-digest"])

        # verify for the sake of ensuring it's right, will throw
        # an exception which should cause a 500 internal server error
        self.ph.verify(hash, req["data"]["password-digest"])

        # new stage
        cur_stage["stage"] = "password-set"
        cur_stage["hash"] = hash

        # set new stage for token
        self.vk.set(f"register:{req['authUser']}", json.dumps(cur_stage))

        del hash
        return rpcs.response(200, {})

    def _setup_otp(self, req: dict) -> str:
        # get current user state from valkey
        cur_stage_raw = self.vk.get(f"register:{req['authUser']}")

        # token either timed out or didn't exist
        if cur_stage_raw is None:
            return rpcs.response(400, {"reason": "Token doesn't exist."})

        # check token at correct stage
        cur_stage = json.loads(cur_stage_raw)
        if cur_stage["stage"] != "password-set":
            return rpcs.response(403, {"reason": "Token not at correct step."})

        # create new secret and make totp provisioning URI with it
        secret = pyotp.random_base32()
        totp = pyotp.totp.TOTP(secret)
        prov_uri = totp.provisioning_uri(
            name=cur_stage["username"],
            issuer_name="App Name Goes Here",
        )

        # new stage info
        cur_stage["stage"] = "setting-up-otp"
        cur_stage["otp_sec"] = secret

        # store new stage info
        self.vk.set(f"register:{req['authUser']}", json.dumps(cur_stage))

        # return provisioning URI (contains secret)
        del secret, totp, cur_stage
        return rpcs.response(200, {"prov_uri": prov_uri})

    def _verify_otp(self, req: dict) -> str:
        # get current user state from valkey
        cur_stage_raw = self.vk.get(f"register:{req['authUser']}")

        # token either timed out or didn't exist
        if cur_stage_raw is None:
            return rpcs.response(400, {"reason": "Token doesn't exist."})

        # check token at correct stage
        cur_stage = json.loads(cur_stage_raw)
        if cur_stage["stage"] != "setting-up-otp":
            return rpcs.response(403, {"reason": "Token not at correct step."})

        # create TOTP with stored secret
        totp = pyotp.totp.TOTP(cur_stage["otp_sec"])

        # check given OTP against stored OTP
        if not totp.verify(req["data"]["otp"]):
            return rpcs.response(400, {"reason": "OTP incorrect."})

        # update stage
        del totp
        cur_stage["stage"] = "otp-verified"

        self.vk.set(f"register:{req['authUser']}", json.dumps(cur_stage))
        del cur_stage

        return rpcs.response(200, {})

    def process(self, body):
        logging.info("[RECEIVED] %s", body)

        # decode json
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Bad JSON."})

        try:
            # check version
            if req["version"] != "1.0.0":
                return rpcs.response(400, {"reason": "Bad version."})

            # do stuff based on step
            match req["data"]["step"]:
                case "check-valid-username":
                    return self._check_valid_username(req)
                case "set-password":
                    return self._set_password(req)
                case "setup-otp":
                    return self._setup_otp(req)
                case "verify-otp":
                    return self._verify_otp(req)
                case _:
                    return rpcs.response(400, {"reason": "Unknown step."})

        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Add appropriate docs here.
    """

    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    vk = valkey.Valkey(
        host="accounts-valkey",
        port="6379",
        db=0,
        username=os.environ["VALKEY_USERNAME"],
        password=os.environ["VALKEY_PASSWORD"],
    )

    rpc_server = RegisterRPCServer(
        valkey=vk,
        rabbitmq_user=os.environ["RABBITMQ_USERNAME"],
        rabbitmq_pass=os.environ["RABBITMQ_PASSWORD"],
        rpc_prefix="register-rpc",
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
