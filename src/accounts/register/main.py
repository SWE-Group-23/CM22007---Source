"""
Handles the multi-stage registration process.
"""

import os
import json
import logging
import re

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
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)
        self.vk = valkey

    def _check_username(self, username: str) -> bool:
        """
        Checks if a username is formatted
        correctly:
            - must be 5 chars or longer
            - must only contain:
                [0-9A-Za-z-_.]
            - cannot begin or end with special chars
        """
        if len(username) <= 5:
            return False

        # can't begin with special characters -_.
        # must only consist of alphanumeric and -_.
        # can't end with special characters -_.
        pattern = re.compile(r"^(?![-_.]).[0-9A-Za-z-_.]+$.*(?<![-_.])$")

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
