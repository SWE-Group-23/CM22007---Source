"""
Gets the profile from the database and returns to the user
"""

import os
import json
import logging

import shared
from shared import rpcs
from shared.models import profile as models

class ViewProfileRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer
    """
    def __init__(self, rabbitmq_user: str, rabbitmq_pass: str, *, rpc_prefix="view-profile-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _view_profile(self, user_id):
        """
        Attempts to fetch profile for a specific user
        """
        try:
            q = models.Profile.objects.filter(username=user_id).get()
            data = {"username": str(q.username),
                     "name": str(q.name),
                     "bio": str(q.bio),
                     "food_preferences": str(q.food_preferences)}
            return rpcs.response(200, {"data": data})
        except IndexError as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
            return rpcs.response(400, {"message": "Unable to fetch profile"})

    def process(self, body):
        logging.info("[RECEIVED] %s", body.decode())

        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Bad JSON."})

        try:
            if req["version"] != "1.0.0":
                return rpcs.response(400, {"reason": "Bad version."})

            resp = rpcs.response(500, {"reason": "Internal Server Error"})

            user_id = req["data"]["username"]
            logging.info("User ID: %s", user_id)

            resp = self._view_profile(user_id)

            return resp
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})

def main():
    """
    Sets up Scylla and the RPC Server, then starts
    consuming the call queue.
    """
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    rpc_server = ViewProfileRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"]
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
