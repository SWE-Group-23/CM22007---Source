"""
Client for using the send message RPC from the
chat subsystem.
"""

import uuid
from shared import rpcs


class SendMessageRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the send message RPC from the
    chat subsystem.
    """
    def __init__(self, *args, rpc_prefix="send-message-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(self, auth_user: str, service: str, chat_id: uuid, send_id: uuid, time_sent: int, message: str, api_version="1.0.0"):
        """
        Calls send message RPC
        """
        try:
            req = rpcs.request(
                auth_user,
                api_version,
                service,
                data = {
                    "chat_id": str(chat_id),
                    "sender_id": str(send_id),
                    "time_sent": time_sent,
                    "message": message
                }
            )
            print(f"Json formatted data: {req}")
        except Exception as e:
            print(f"Error calling rpcs.request(): {e}")

        return self._call(body=req)