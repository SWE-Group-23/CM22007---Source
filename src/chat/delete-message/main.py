"""
Deletes a specific message from the database
"""

import os
import json
import logging
import uuid

import shared
from shared import rpcs
from shared.models import chat as models


class DeleteMessageRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        *,
        rpc_prefix="delete-message-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _delete_message(self, msg_id):
        """
        Attempts to delete a specific message from the database
        """
        msg = models.Messages.objects.get(msg_id=msg_id)
        if msg:
            msg.delete()
            return rpcs.response(200, {"message": "Success"})

        logging.error("[DB ERROR] Cannot find message to delete")
        return rpcs.response(400, {"message": "Unable to delete message"})

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

            msg_id = uuid.UUID(req["data"]["msg_id"])

            logging.info("Message ID: %s", msg_id)

            resp = self._delete_message(msg_id)

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

    rpc_server = DeleteMessageRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
