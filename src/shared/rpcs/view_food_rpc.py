"""
Defines RPC client for the View Food RPC.
"""

import uuid
from datetime import datetime

from shared import rpcs


class ViewFoodRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which views all food items
    in a user's inventory.
    """

    def call(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        auth_user: str,
        srv_from: str,
        api_version="1.0.0",
    ) -> bytes:
        """
        Calls View Food RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
        )

        return self._call(body=req)
