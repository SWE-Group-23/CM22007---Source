"""
Client for using the delete message RPC from the
chat subsystem.
"""

import uuid
from shared import rpcs

class DeleteMessageRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the delete message RPC from the
    chat subsystem.
    """
    def __init__(self, *args, rpc_prefix="delete-message-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(self, auth_user: str, service: str, msg_id: uuid, api_version="1.0.0"):
        """
        Calls delete message RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "msg_id": str(msg_id)
            }
        )

        return self._call(body=req)
