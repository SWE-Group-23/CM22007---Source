"""
Client for using the fetch messages RPC from the
chat subsystem.
"""

import uuid
from shared import rpcs

class FetchMessagesRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the fetch messages RPC from the
    chat subsystem.
    """
    def __init__(self, *args, rpc_prefix="fetch-messages-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(self, auth_user: str, service: str, chat_id: uuid, api_version="1.0.0"):
        """
        Calls fetch messages RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "chat_id": str(chat_id)
            }
        )

        return self._call(body=req)
