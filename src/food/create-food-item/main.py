"""
Adds a food item to the user's private inventory.
"""

import json
import logging
import os
import uuid
from datetime import datetime

import shared
from shared import rpcs
from shared.models import food as models


class CreateFoodRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which creates food items.
    """

    def __init__(
        self,
        rabbitmq_user,
        rabbitmq_pass,
        rpc_prefix="create-food-item-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def create_food_item(
        self,
        auth_user: str,
        img_id: uuid.UUID,
        label: str,
        description: str,
        useby: datetime,
    ) -> str:
        """
        Attempts to add a new food item to the user's inventory.
        """
        if useby < datetime.now():
            return rpcs.response(
                400, {"reason": "Expiry datetime cannot be before now."}
            )

        models.Food.if_not_exists().create(
            user=auth_user,
            img_id=img_id,
            label=label,
            description=description,
            useby=useby,
        )

        return rpcs.response(
            200,
            {"message": "Successfully created food item."},
        )

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

            img_id = None
            if (img_id_str := req["data"].get("img_id")) is not None:
                img_id = uuid.UUID(img_id_str)

            label = req["data"]["label"]
            description = req["data"].get("description")
            useby = datetime.fromisoformat(req["data"]["useby"])

            return self.create_food_item(
                auth_user=req["authUser"],
                img_id=img_id,
                label=label,
                description=description,
                useby=useby,
            )
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


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
