"""
Handles the multi-stage login process.
"""

import os
import logging
import json

import argon2
import valkey

import shared
from shared import rpcs
from shared.models import accounts as model


class LoginRPCServer(rpcs.RPCServer):
    """
    Serves the login RPC.
    """

    def __init__(
        self,
        vk,
        rabbitmq_user,
        rabbitmq_pass,
        *,
        rpc_prefix="login-rpc"
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)
        self.vk = vk
        self.ph = argon2.PasswordHasher()

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
