"""
Add some service docs here.
"""

import os
import logging
import json
from shared.models import profile as model

import shared
from shared import rpcs

class CreateProfileRPCServer(rpcs.RPCServer):
    """
    Serves the create profile RPC.
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        *,
        rpc_prefix="create-profile-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _add_profile(self, data: dict) -> str:
        """
        Adds profile data to database
        """
        (
            model.Profile.if_not_exists().create(
                username=data["username"],
                name=data["name"],
                bio=data["bio"],
                food_preferences=data["food_preferences"]
            )
        )
        return rpcs.response(200, {"status": "success"})

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

            # return response
            return self._add_profile(req["data"])

        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})

def main():
    """
    Connects to ScyllaDB
    """
    logging.info("Connecting to ScyllaDB...")
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    rpc_server = CreateProfileRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"]
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
