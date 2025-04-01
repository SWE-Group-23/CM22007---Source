"""
Client for using the view chats RPC from the
chat subsystem.
"""

from shared import rpcs

class ViewChatsRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the view chats RPC from the
    chat subsystem.
    """
    def __init__(self, *args, rpc_prefix="view-chats-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(self, auth_user: str, service: str, user_id: str, api_version="1.0.0"):
        """
        Calls view chats RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "user_id": str(user_id)
            }
        )

        return self._call(body=req)
