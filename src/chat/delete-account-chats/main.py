"""
Deletes a chats associated with an account
"""

import os
import json
import logging

import shared
from shared import rpcs
from shared.models import chat as models

class DeleteAccountChatsRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer
    """
    def __init__(self, rabbitmq_user: str,
                 rabbitmq_pass: str,
                 *,
                 rpc_prefix="delete-account-chats-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _delete_chats(self, username):
        """
        Deletes associated chats with a user
        """
        success = False
        q1 = models.Chats.objects.filter(user1=username)
        q2 = models.Chats.objects.filter(user2=username)
        for chat in q1:
            chat.delete()
            success = True
        for chat in q2:
            chat.delete()
            success = True

        if success:
            return rpcs.response(200, {"message": "Success"})

        logging.error("[DB ERROR] Cannot find chats to delete")
        return rpcs.response(400, {"message": "Unable to delete chats"})

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

            resp = self._delete_chats(username)

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

    rpc_server = DeleteAccountChatsRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"]
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
