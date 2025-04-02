"""
Updates an existing food item in the user's private inventory.
"""

import os
import logging
import json

import uuid
from datetime import datetime

import shared
from shared import rpcs


class UpdateFoodRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which updates existing food items.
    """

    def __init__(
        self,
        rabbitmq_user,
        rabbitmq_pass,
        rpc_prefix="update-food-item-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def update_food_item():
        pass

    def process(self, body):
        logging.info("[RECEIVED] %s", body.decode())

        # check json parses
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Bad JSON."})

        # parse message
        try:
            # version checking
            if req["version"] != "1.0.0":
                return rpcs.response(400, {"reason": "Bad version."})

            response = rpcs.response(500, {"reason": "Internal Server Error"})

            # get all the info from server
            # call update food item

            return response
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Connects Update Food RPC to ScyllaDB and creates corresponding RPC Server.
    """

    # setup database session
    logging.info("Connecting to ScyllaDB...")
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # create food rpc
    logging.info("Making UpdateFoodRPCServer...")
    rpc_server = UpdateFoodRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
    )

    # consuming...
    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
