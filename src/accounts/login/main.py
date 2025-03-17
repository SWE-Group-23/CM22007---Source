"""
Handles the multi-stage login process.
"""

import os
import logging
import json

import argon2
import valkey
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
                    pw_hash, req["data"]["password_digest"])
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
                req["data"]["password_digest"])
            user.save()

        login_success = (True if user is not None else False) and pw_correct

        del pw_hash, user

        if login_success:
            stage = {"stage": "username-password",
                     "username": req["data"]["username"]}
            self.vk.setex(f"login:{req['authUser']}",
                          60 * 30, json.dumps(stage))

        return rpcs.response(200, {"correct": login_success})

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
