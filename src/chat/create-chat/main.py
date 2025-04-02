"""
Creates a new chat between two users
"""

import os
import json
import logging

import shared
from shared import rpcs
from shared.models import chat as models


class CreateChatRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        *,
        rpc_prefix="create-chat-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _new_chat(self, sender_user, receiver_user):
        """
        Creates a new chat
        """
        models.Chats.create(user1=sender_user, user2=receiver_user)
        return rpcs.response(200, {"message": "Success"})

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

            sender_user = str(req["authUser"])
            receiver_user = str(req["data"]["receiver_user"])

            resp = self._new_chat(sender_user, receiver_user)

            return resp

        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Sets up Scylla, and the RPC Server, then starts
    consuming the call queue.
    """
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    rpc_server = CreateChatRPCServer(
        os.environ["RABBITMQ_USERNAME"], os.environ["RABBITMQ_PASSWORD"]
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
