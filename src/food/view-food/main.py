"""
Views all uploaded food for a user.
"""

import os
import logging
import json 

from datetime import datetime

import shared
from shared import rpcs
from shared.models import food as models

class ViewFoodRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which views current food table.
    """
    def __init__(self, rabbitmq_user, rabbitmq_pass, rpc_prefix="view-food-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)
    
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

            foods = models.Food.objects.filter(
                user=req["authUser"],
            )

            if foods:
                data = {
                    "foods": [
                        {
                            "food_id": str(food.food_id),
                            "img_id": str(food.img_id),
                            "label": str(food.label),
                            "useby": str(food.userby),
                        }
                        for food in foods
                    ]
                }
                return rpcs.response(200, data)

            return rpcs.response(200, {})
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Connects View Food RPC to ScyllaDB and creates corresponding RPC Server.
    """

    # setup database session
    logging.info("Connecting to ScyllaDB...")
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # create food rpc
    logging.info("Making ViewFoodRPCServer...")
    rpc_server = ViewFoodRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
    )

    # consuming...
    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
