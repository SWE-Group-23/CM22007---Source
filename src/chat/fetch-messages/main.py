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
    def __init__(self, rabbitmq_user: str, rabbitmq_pass: str, *, rpc_prefix="fetch-messages-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def _fetch_messages(self, chat_id):
        """
        Attempts to fetch all messages from a specific chat
        """
        try:
            q = models.Messages.objects.filter(chat_id=chat_id)
            data = [{"msg_id": msg.msg_id, 
                     "chat_id": msg.chat_id,
                     "sender_id": msg.sender_id,
                     "sent_time": msg.sent_time,
                     "message": msg.message, 
                     "reported": msg.reported} 
                     for msg in q]
            return rpcs.response(200, {"data": data})
        except Exception as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
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
    # Set up database session
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    rpc_server = FetchMessagesRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"]
    )

    
    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
