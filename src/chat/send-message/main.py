"""
Add some service docs here.
"""

import os
import json
import logging

import shared
from shared import rpcs
from shared.models import chat as models

class SendMessageRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer ...
    """
    def __init__(self, rabbitmq_user: str, rabbitmq_pass: str, *, rpc_prefix="send-message-rpc",):
        logging.info("Initialised...")
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _add_message(self, chat_id, sender_id, time_sent, message):
        """
        Lil description
        """
        try:
            models.Messages.create(
                chat_id = chat_id,
                sender_id = sender_id,
                sent_time = time_sent,
                message = message
            )
            return rpcs.response(200, {"message": "Message sent"})
        except Exception as e:
            return rpcs.response(400, {"message": "Unable to send message"})

    def process(self, body, *args, **kwargs):
        """
        Docs
        """
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
            sender_id = req["data"]["sender_id"]
            time_sent = req["data"]["time_sent"]
            message= req["data"]["message"]

            resp = self._add_message(chat_id, sender_id, time_sent, message)

            return resp
        
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})
        
    

def main():
    """
    Add appropriate docs here.
    """
    # Set up database session
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    rpc_server = SendMessageRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"]
    )

    
    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
