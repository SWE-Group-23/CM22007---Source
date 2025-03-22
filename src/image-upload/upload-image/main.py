
import os
import logging
import uuid
from datetime import datetime

import shared
from shared import rpcs
from shared.models import food as models
import json


class ImageRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which creates image items when added.
    """
    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        rpc_prefix="create-image-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)
    
    def _add_image(self, image_id, user_id, food_name) -> str:

        (
            model.Image.if_not_exists().create(
                food_id = data["food_id"],
                user_id = data["user_id"],
                label = data["food_name"],
                img_id = data["img_id"]
            )
            return rpcs.response(200, {"message" : "Successfully created Image item"})

        except Exception as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
            return rpcs.response(400, {"reason": "Unable to create Image item"})
    
    def process(self, body):
        logging.info("[RECEIVED] %s", body.decode())

        # check json parses
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Bad JSON."})

        try:
            if req["version"] != "1.0.0":
                return rpcs.response(400, {"reason": "Bad version."})

            response = rpcs.response(500, {"reason": "Internal Server Error"})

            user_id = uuid.UUID(req["data"]["user_id"])
            food_id = uuid.UUID(req["data"]["food_id"])
            img_id = uuid.UUID(req["data"]["img_id"])
            label = req["data"]["label"]

            response = self.create_food_item(food_id, user_id, label, useby_date, img_id)
            
            return response
        except KeyError:
            return rpcs.response(400,{"reason": "Malformed request."})



def main():
    """
    Add appropriate docs here.
    """

    # setup database session 
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # create image rpc
    rpc_server = ImageRPCServer(
       os.environ["RABBITMQ_USERNAME"],
       os.environ["RABBITMQ_PASSWORD"],
    )

    # consuming...
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    main()