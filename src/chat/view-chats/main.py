"""
Gets the chats from the database and returns to the user
"""

import os
import json
import logging

import shared
from shared import rpcs
from shared.models import chat as models

class ViewChatsRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer
    """
    def __init__(self, rabbitmq_user: str, rabbitmq_pass: str, *, rpc_prefix="view-chats-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _fetch_chats(self, user):
        """
        Attempts to fetch all chats for a specific user
        """
        try:
            q1 = list(models.Chats.objects.filter(user1=user))
            q2 = list(models.Chats.objects.filter(user2=user))
            q = q1 + q2
            data = [{"chat_id": str(chat.chat_id),
                     "user1": chat.user1,
                     "user2": chat.user2,
                     "blocked": str(chat.blocked)}
                     for chat in q]
            return rpcs.response(200, data)
        except q1.DoesNotExist as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
            return rpcs.response(400, {"message": "Unable to fetch chats"})

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

            username = str(req["authUser"])
            logging.info("User: %s", username)

            resp = self._fetch_chats(username)

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

    rpc_server = ViewChatsRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"]
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
