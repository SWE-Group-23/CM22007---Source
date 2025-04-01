"""
Client for using the delete account chats RPC from the
chat subsystem.
"""

from shared import rpcs

class DeleteAccountChatsRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the delete account chats RPC from the
    chat subsystem.
    """
    def __init__(self, *args, rpc_prefix="delete-account-chats-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(self, auth_user: str, service: str, username: str, api_version="1.0.0"):
        """
        Calls delete account chats RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "username": username
            }
        )

        return self._call(body=req)
