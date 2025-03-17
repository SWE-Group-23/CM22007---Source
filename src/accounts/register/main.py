"""
Handles the multi-stage registration process.

TODO: allow a user to go back through stages if needed.
"""

import os
import json
import logging
import re
import secrets
import datetime

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

    def __init__(
        self,
        vk,
        rabbitmq_user,
        rabbitmq_pass,
        *,
        rpc_prefix="register-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)
        self.vk = vk
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

    def _check_stage(
        self,
        req: dict,
        stage: str,
    ) -> tuple[str | None, None | dict]:
        """
        Checks if the token is at the correct stage,
        returning either an error response or the
        current stage.
        """
        cur_stage_raw = self.vk.get(f"register:{req['authUser']}")

        if cur_stage_raw is None:
            return (
                rpcs.response(400, {"reason": "Token doesn't exist."}),
                None,
            )

        cur_stage = json.loads(cur_stage_raw)
        if cur_stage["stage"] != stage:
            return (
                rpcs.response(403, {"reason": "Token not at correct step."}),
                None,
            )

        return None, cur_stage

    def _check_valid_username(self, req: dict) -> str:
        """
        Checks if a username already exists
        or is formatted correctly
        and creates a JSON response based
        on if it does.
        """

        # check if already past this step
        if self.vk.get(f"register:{req['authUser']}") is not None:
            return rpcs.response(403, {"reason": "Token not at correct step."})

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
        """
        Hashes password digest and stores
        it in the token's Valkey stage,
        updating the step.
        """

        # check at correct stage
        err, cur_stage = self._check_stage(req, "username-valid")
        if err:
            return err

        # hash+salt password with argon2
        pw_hash = self.ph.hash(req["data"]["password-digest"])

        # verify for the sake of ensuring it's right, will throw
        # an exception which should cause a 500 internal server error
        self.ph.verify(pw_hash, req["data"]["password-digest"])

        # new stage
        cur_stage["stage"] = "password-set"
        cur_stage["hash"] = pw_hash

        # set new stage for token
        self.vk.set(f"register:{req['authUser']}", json.dumps(cur_stage))

        del pw_hash
        return rpcs.response(200, {})

    def _setup_otp(self, req: dict) -> str:
        """
        Generates an OTP secret for a token,
        stores it in the token's Valkey stage,
        updating the step. Sends provisioning
        URI.
        """
        # check at correct stage
        err, cur_stage = self._check_stage(req, "password-set")
        if err:
            return err

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
        """
        Verifies that the user has their
        OTP set up correctly by checking
        an OTP against the stored one.
        Updates tokens step in Valkey stage.
        """
        # check at correct stage
        err, cur_stage = self._check_stage(req, "setting-up-otp")
        if err:
            return err

        # create TOTP with stored secret
        totp = pyotp.totp.TOTP(cur_stage["otp_sec"])

        # check given OTP against stored OTP
        if not totp.verify(req["data"]["otp"], valid_window=1):
            return rpcs.response(400, {"reason": "OTP incorrect."})

        # update stage
        del totp
        cur_stage["stage"] = "otp-verified"

        self.vk.set(f"register:{req['authUser']}", json.dumps(cur_stage))
        del cur_stage

        return rpcs.response(200, {})

    def _backup_code(self, req: dict) -> str:
        """
        Generates backup codes and gives them
        to the user, then adds their account
        to the database, removing their stage
        from Valkey.
        """
        # check at correct stage
        err, cur_stage = self._check_stage(req, "otp-verified")
        if err:
            return err

        # generate backup code
        backup_code = (
            secrets.token_hex(8)
            + "-"
            + secrets.token_hex(8)
            + "-"
            + secrets.token_hex(8)
            + "-"
            + secrets.token_hex(8)
        )

        # hash backup code for storage
        backup_hash = self.ph.hash(backup_code)
        self.ph.verify(backup_hash, backup_code)

        # add user to database
        (
            model.Accounts.if_not_exists().create(
                username=cur_stage["username"],
                password_hash=cur_stage["hash"],
                otp_secret=cur_stage["otp_sec"],
                backup_code_hash=backup_hash,
                created_at=datetime.datetime.now(),
            )
        )

        # delete user stage in valkey
        self.vk.delete(f"register:{req['authUser']}")

        return rpcs.response(200, {"backup_code": backup_code})

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

            # default response is error, should never get returned
            resp = rpcs.response(500, {"reason": "Internal Server Error"})

            # get response based on step
            match req["data"]["step"]:
                case "check-valid-username":
                    resp = self._check_valid_username(req)
                case "set-password":
                    resp = self._set_password(req)
                case "setup-otp":
                    resp = self._setup_otp(req)
                case "verify-otp":
                    resp = self._verify_otp(req)
                case "backup-code":
                    resp = self._backup_code(req)
                case _:
                    resp = rpcs.response(400, {"reason": "Unknown step."})

            # return response
            return resp

        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Sets up Scylla, Valkey, and the RPC server, then starts consuming
    the RPC call queue.
    """

    logging.info("Connecting to ScyllaDB...")
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    logging.info("Connecting to Valkey...")
    vk = valkey.Valkey(
        host="accounts-valkey",
        port="6379",
        db=0,
        username=os.environ["VALKEY_USERNAME"],
        password=os.environ["VALKEY_PASSWORD"],
    )

    logging.info("Setting up RPC server...")
    rpc_server = RegisterRPCServer(
        vk=vk,
        rabbitmq_user=os.environ["RABBITMQ_USERNAME"],
        rabbitmq_pass=os.environ["RABBITMQ_PASSWORD"],
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
