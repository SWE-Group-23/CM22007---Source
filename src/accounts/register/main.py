"""
Handles the multi-stage registration process.
"""

import os
import json
import logging

import valkey
from cassandra.cqlengine import query

import shared
from shared import rpcs
from shared.models import accounts as model


class RegisterRPCServer(rpcs.RPCServer):
    """
    Serves the register RPC.
    """

    def __init__(self, valkey, rabbitmq_user, rabbitmq_pass, rpc_prefix):
        super().__init__(
            rabbitmq_user,
            rabbitmq_pass,
            rpc_prefix
        )
        self.vk = valkey

    def _check_unique(self, req: dict) -> str:
        """
        Checks if a username already exists
        and creates a JSON response based
        on if it does.
        """
        try:
            model.Accounts.get(
                username=req["data"]["username"]
            )

            return rpcs.response(
                200,
                {"unique": False}
            )

        # couldn't get user with username
        except query.DoesNotExist:
            return rpcs.response(
                200,
                {"unique": True}
            )

    def process(self, body):
        # decode json
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(
                400,
                {"reason": "Bad JSON."}
            )

        try:
            # check version
            if req["version"] != "1.0.0":
                return rpcs.response(
                    400,
                    {"reason": "Bad version."}
                )

            # do stuff based on step
            match req["data"]["step"]:
                case "check-unique":
                    return self._check_unique(req)
                case _:
                    return rpcs.response(
                        400,
                        {"reason": "Unknown step."}
                    )

        except KeyError:
            return rpcs.response(
                400,
                {"reason": "Malformed request."}
            )


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
        rpc_prefix="register-rpc"
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
