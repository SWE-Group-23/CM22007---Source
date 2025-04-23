"""
Handles changing a users authentication factors given at least two correct
factors.
"""

import os
import json
import logging

import shared
from shared import rpcs
from shared.models import accounts as model

import valkey
import argon2
import pyotp


class ChangeAuthRPCServer(rpcs.RPCServer):
    """
    Serves the change auth RPC.
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        vk: valkey.Valkey,
        *,
        rpc_prefix="change-auth-rpc",
    ):
        self.vk = vk
        self.ph = argon2.PasswordHasher()
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _auth_backup_password(
        self,
        *,
        pw_hash: str,
        backup_code: str,
        username: str,
        sid: str,
    ) -> str:
        # get user account
        user = model.Accounts.get(username=username)
        if user is None:
            return rpcs.response(200, {"correct": False})

        # check password
        try:
            valid_pw = self.ph.verify(
                user["password_hash"],
                pw_hash,
            )
        except argon2.exceptions.VerifyMismatchError:
            valid_pw = False

        # check backup code
        try:
            valid_backup = self.ph.verify(
                user["backup_code_hash"],
                backup_code,
            )
        except argon2.exceptions.VerifyMismatchError:
            valid_backup = False

        # use bitwise and to prevent short-circuiting
        if not (valid_backup & valid_pw):
            return rpcs.response(200, {"correct": False})

        # set sid to be authenticated
        self.vk.set(
            f"change-auth:{sid}",
            json.dumps(
                {
                    "username": username,
                    "authenticated": True,
                    "needs-otp": False,
                }
            ),
            keepttl=True,
        )

        return rpcs.response(200, {"correct": True})

    def _auth_backup_otp(
        self,
        *,
        backup_code: str,
        username: str,
        sid: str,
    ) -> str:
        # get user account
        user = model.Accounts.get(username=username)
        if user is None:
            return rpcs.response(200, {"correct": False})

        # check backup code
        try:
            self.ph.verify(
                user["backup_code_hash"],
                backup_code,
            )
        except argon2.exceptions.VerifyMismatchError:
            return rpcs.response(200, {"correct": False})

        # set sid to be needing OTP
        self.vk.set(
            f"change-auth:{sid}",
            json.dumps(
                {
                    "username": username,
                    "authenticated": False,
                    "needs-otp": True,
                }
            ),
            keepttl=True,
        )

        return rpcs.response(200, {"correct": True})

    def _auth_password_otp(
        self,
        *,
        pw_hash: str,
        username: str,
        sid: str,
    ) -> str:
        # get user account
        user = model.Accounts.get(username=username)
        if user is None:
            return rpcs.response(200, {"correct": False})

        # check password
        try:
            self.ph.verify(
                user["password_hash"],
                pw_hash,
            )
        except argon2.exceptions.VerifyMismatchError:
            return rpcs.response(200, {"correct": False})

        # set sid to be needing OTP
        self.vk.set(
            f"change-auth:{sid}",
            json.dumps(
                {
                    "username": username,
                    "authenticated": False,
                    "needs-otp": True,
                }
            ),
            keepttl=True,
        )

        return rpcs.response(200, {"correct": True})

    def _auth_otp(
        self,
        *,
        otp: str,
        username: str,
        sid: str,
    ) -> str:
        # get user account
        user = model.Accounts.get(username=username)
        if user is None:
            return rpcs.response(200, {"correct": False})

        totp = pyotp.totp.TOTP(user["otp_secret"])

        if not totp.verify(
            str(otp).zfill(6),
            valid_window=1,
        ):
            return rpcs.response(200, {"correct": False})

        # set sid to be authenticated
        self.vk.set(
            f"change-auth:{sid}",
            json.dumps(
                {
                    "username": username,
                    "authenticated": True,
                    "needs-otp": False,
                }
            ),
            keepttl=True,
        )

        return rpcs.response(200, {"correct": True})

    def _handle_authentication(self, req: dict) -> str:
        # get valkey stage, if the user is authenticated, a gateway should send
        # the request with their 'sid' rather than 'authUser'.
        stage = json.loads(self.vk.get(f"change-auth:{req['sid']}"))

        # create new blank stage with 5 min timeout if it doesn't exist
        if stage is None:
            stage = {}
            self.vk.set(
                f"change-auth:{req['sid']}",
                json.dumps(stage),
                ex=60 * 5,
            )

        # get username from stage or request if it's there
        username = stage.get("username") or req["data"].get("username")
        if username is None:
            return rpcs.response(400, {"reason": "Could not find username."})

        # default response is error, should never get returned
        resp = rpcs.response(500, {"reason": "Internal Server Error"})

        # process specific action
        match req["data"]["factors"]:
            case "backup-password":
                resp = self._auth_backup_password(
                    pw_hash=req["data"]["password-digest"],
                    backup_code=req["data"]["backup-code"],
                    username=username,
                    sid=req["sid"],
                )
            case "backup-otp":
                resp = self._auth_backup_otp(
                    backup_code=req["data"]["backup-code"],
                    username=username,
                    sid=req["sid"],
                )
            case "password-otp":
                resp = self._auth_password_otp(
                    backup_code=req["data"]["password-digest"],
                    username=username,
                    sid=req["sid"],
                )
            case "otp" if stage.get("needs-otp"):
                resp = self._auth_otp(
                    otp=req["data"]["otp"],
                    username=username,
                    sid=req["sid"],
                )
            case "otp" if not stage.get("needs-otp"):
                resp = rpcs.response(
                    403,
                    {"reason": "Session at incorrect stage."},
                )
            case _:
                resp = rpcs.response(400, {"reason": "Malformed request."})

        return resp

    def _handle_change(self, req: dict) -> str:
        # first check accounts valkey to make sure the user has authenticated
        # for changing their auth
        pass

    def process(self, body: bytes) -> str:
        logging.info("[RECEIVED] %s", body)

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

            # choose how to handle based on what's in data
            if "factors" in req["data"].keys():
                resp = self._handle_authentication(req)
            elif "change" in req["data"].keys():
                resp = self._handle_change(req)
            else:
                resp = rpcs.response(400, {"reason": "Malformed request."})

            return resp
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Connect to ScyllaDB, Valkey, and start running the RPC server.
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
    rpc_server = ChangeAuthRPCServer(
        vk=vk,
        rabbitmq_user=os.environ["RABBITMQ_USERNAME"],
        rabbitmq_pass=os.environ["RABBITMQ_PASSWORD"],
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
