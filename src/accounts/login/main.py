"""
Handles the multi-stage login process.
"""

import os
import logging
import json
import datetime

import argon2
import valkey
import pyotp
from cassandra.cqlengine import query

import shared
from shared import rpcs
from shared.models import accounts as model


class LoginRPCServer(rpcs.RPCServer):
    """
    Serves the login RPC.
    """

    def __init__(
        self,
        vk: valkey.Valkey,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        *,
        rpc_prefix="login-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)
        self.vk = vk
        self.ph = argon2.PasswordHasher()

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
        cur_stage_raw = self.vk.get(f"login:{req['authUser']}")

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

    def _username_password(self, req: dict) -> str:
        """
        Handles the first stage of the login
        process where the username and
        password are entered.

        NOTE: This is not designed to be
        secure against side-channel attacks.
        """
        # check if token at correct step
        if self.vk.get(f"login:{req['authUser']}") is not None:
            return rpcs.response(403, {"reason": "Token not at correct step."})

        try:
            user = model.Accounts.get(username=req["data"]["username"])
            pw_hash = user["password_hash"]

            try:
                pw_correct = self.ph.verify(
                    pw_hash,
                    req["data"]["password_digest"],
                )
            except argon2.exceptions.VerifyMismatchError:
                pw_correct = False

        except query.DoesNotExist:
            user = None
            pw_hash = None
            pw_correct = False

        # if password is correct and needs rehash,
        # we should do it now while we have it
        if pw_correct and self.ph.check_needs_rehash(pw_hash):
            user["password_hash"] = self.ph.hash(
                req["data"]["password_digest"],
            )
            user.save()

        login_success = (user is not None) and pw_correct

        del pw_hash, user

        if login_success:
            stage = {
                "stage": "username-password",
                "username": req["data"]["username"],
            }
            self.vk.setex(
                f"login:{req['authUser']}",
                60 * 30,
                json.dumps(stage),
            )

        return rpcs.response(200, {"correct": login_success})

    def _verify_otp(self, req: dict) -> str:
        """
        Verifies that a user has
        input the correct OTP.
        """
        # check at correct stage
        err, cur_stage = self._check_stage(req, "username-password")
        if err:
            return err

        if not (
            isinstance(
                req["data"]["otp"],
                int,
            )
            or isinstance(
                req["data"]["otp"],
                str,
            )
        ):
            del cur_stage
            return rpcs.response(400, {"reason": "Malformed request."})

        try:
            otp_sec = (
                model.Accounts.objects()
                .only(
                    ["otp_secret"],
                )
                .get(
                    username=cur_stage["username"],
                )["otp_secret"]
            )
        except query.DoesNotExist:
            self.vk.delete(f"login:{req['authUser']}")
            return rpcs.response(400, {"reason": "User no longer exists."})

        # create TOTP with stored secret
        totp = pyotp.totp.TOTP(otp_sec)

        # check given OTP against stored OTP
        if not totp.verify(req["data"]["otp"], valid_window=1):
            del totp, cur_stage, otp_sec
            return rpcs.response(200, {"correct": False})

        # OTP correct so clean up
        self.vk.delete(f"login:{req['authUser']}")

        # set last login
        model.Accounts.get(
            username=cur_stage["username"],
        ).update(last_login=datetime.datetime.now())

        del totp, cur_stage, otp_sec
        return rpcs.response(200, {"correct": True})

    def process(self, body: bytes) -> str:
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
                case "username-password":
                    resp = self._username_password(req)
                case "verify-otp":
                    resp = self._verify_otp(req)
                case _:
                    resp = rpcs.response(400, {"reason": "Unknown step."})

            # return response
            return resp

        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Sets up Scylla, Valkey, the RPC Server, and then starts
    consuming the call queue.
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
    rpc_server = LoginRPCServer(
        vk=vk,
        rabbitmq_user=os.environ["RABBITMQ_USERNAME"],
        rabbitmq_pass=os.environ["RABBITMQ_PASSWORD"],
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
