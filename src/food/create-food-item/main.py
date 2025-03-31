"""
Adds a food item to the user's private inventory.
"""
import json
import os
import logging
import uuid
from datetime import datetime

import shared
from shared import rpcs
from shared.models import food as models


class CreateFoodRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which creates food items when added.
    """

    def __init__(self, rabbitmq_user, rabbitmq_pass, rpc_prefix="create-food-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def create_food_item(self, user_id, img_id, food_name, useby):
        """
        Attempts to add a new food item to the user's inventory.
        """
        if useby < datetime.now():
            return rpcs.response(400, {"reason": "Unable to create food item - Already expired"})
  
        try:
            models.Food.if_not_exists().create(
                user_id = user_id,
                img_id = img_id,
                label = food_name,
                useby = useby
            )
            return rpcs.response(200, {"message" : "Successfully created food item"})
        except Exception as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
            return rpcs.response(400, {"reason": "Unable to create food item"})

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

            user_id = uuid.UUID(req["data"]["user_id"])
            img_id = uuid.UUID(req["data"]["img_id"])
            label = req["data"]["label"]
            useby = datetime.fromisoformat(req["data"]["useby"])

            response = self.create_food_item(user_id, img_id, label, useby)

            return response
        except KeyError:
            return rpcs.response(400,{"reason": "Malformed request."})



def main():
    """
    Connects Create Food RPC to ScyllaDB and creates corresponding RPC Server.
    """

    # setup database session
    logging.info("Connecting to ScyllaDB...")
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # create food rpc
    logging.info("Making CreateFoodRPCServer...")
    rpc_server = CreateFoodRPCServer(
       os.environ["RABBITMQ_USERNAME"],
       os.environ["RABBITMQ_PASSWORD"],
    )

    # consuming...
    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
