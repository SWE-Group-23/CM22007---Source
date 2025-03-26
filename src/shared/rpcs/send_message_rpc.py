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

    def call(   # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            auth_user: str,
            service: str,
            chat_id,
            send_id: uuid,
            receiver_id: uuid,
            time_sent: int,
            message: str,
            api_version="1.0.0"):
        """
        Calls send message RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "chat_id": str(chat_id),
                "sender_id": str(send_id),
                "receiver_id": str(receiver_id),
                "time_sent": time_sent,
                "message": message
            }
        )

        return self._call(body=req)
