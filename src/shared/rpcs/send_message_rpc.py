"""
Client for using the send message RPC from the
chat subsystem.
"""

import json
import uuid
from shared import rpcs


class SendMessageRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the send message RPC from the
    chat subsystem.
    """

    def call(self, auth_user: str, service: str, chat_id: uuid, send_id: uuid, time_sent: int, message: str, api_version="1.0.0"):
        """
        Docs
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "chat_id": chat_id,
                "sender_id": send_id,
                "time_sent": time_sent,
                "message": message
            }
        )

        return self._call(body=req)