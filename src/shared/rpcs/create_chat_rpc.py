"""
Client for using the create chat RPC from the
chat subsystem.
"""

from shared import rpcs

class CreateChatRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the create chats RPC from the
    chat subsystem.
    """
    def __init__(self, *args, rpc_prefix="create-chat-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(self, auth_user: str, service: str, receiver_user:str, api_version="1.0.0"):
        """
        Calls view chats RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "receiver_user": str(receiver_user)
            }
        )

        return self._call(body=req)
