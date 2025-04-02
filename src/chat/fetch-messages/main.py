"""
Gets the messages from the database and returns to the user
"""

import os
import json
import logging
import uuid

import shared
from shared import rpcs
from shared.models import chat as models


class FetchMessagesRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        *,
        rpc_prefix="fetch-messages-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _fetch_messages(self, chat_id):
        """
        Attempts to fetch all messages from a specific chat
        """
        q = models.Messages.objects.filter(chat_id=chat_id)
        if q:
            data = [
                {
                    "msg_id": str(msg.msg_id),
                    "chat_id": str(msg.chat_id),
                    "sender_user": str(msg.sender_user),
                    "sent_time": str(msg.sent_time),
                    "message": str(msg.message),
                    "reported": str(msg.reported),
                }
                for msg in q
            ]
            return rpcs.response(200, {"data": data})
        logging.error("[DB ERROR] Could not get messages")
        return rpcs.response(400, {"message": "Unable to fetch messages"})

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

            chat_id = uuid.UUID(req["data"]["chat_id"])

            resp = self._fetch_messages(chat_id)

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

    rpc_server = FetchMessagesRPCServer(
        os.environ["RABBITMQ_USERNAME"], os.environ["RABBITMQ_PASSWORD"]
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
