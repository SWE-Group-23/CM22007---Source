"""
Handles a message sent by the user
"""

import os
import json
import logging
import uuid
from datetime import datetime

import shared
from shared import rpcs
from shared.models import chat as models


class SendMessageRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        *,
        rpc_prefix="send-message-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _add_message(self, chat_id, sender_user, time_sent, message):
        """
        Attempts to add a message to the messages table
        """
        try:
            models.Messages.create(
                chat_id=chat_id,
                sender_user=sender_user,
                sent_time=time_sent,
                message=message,
            )
            return rpcs.response(200, {"message": "Message sent"})
        except ConnectionError as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
            return rpcs.response(400, {"message": "Unable to send message"})

    def _new_chat(self, sender_user, receiver_user):
        """
        Creates a new chat if there was not an existing one
        """
        chat = models.Chats.create(user1=sender_user, user2=receiver_user)
        return chat.chat_id

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

            chat_id = req["data"]["chat_id"]
            sender_user = str(req["authUser"])
            receiver_user = str(req["data"]["receiver_user"])
            time_sent = datetime.strptime(req["data"]["time"], "%Y-%m-%d %H:%M:%S.%f")
            message= req["data"]["message"]

            if chat_id != "None":
                chat_id = uuid.UUID(chat_id)
            else:
                chat_id = self._new_chat(sender_user, receiver_user)

            resp = self._add_message(chat_id, sender_user, time_sent, message)

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

    rpc_server = SendMessageRPCServer(
        os.environ["RABBITMQ_USERNAME"], os.environ["RABBITMQ_PASSWORD"]
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
