"""
Client for using the view profile RPC from the
profile subsystem.
"""

import uuid
from shared import rpcs

class ViewProfileRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the view profile RPC from the
    profile subsystem.
    """
    def __init__(self, *args, rpc_prefix="view-profile-rpc", **kwargs):
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
                "username": user_id
            }
        )

        return self._call(body=req)