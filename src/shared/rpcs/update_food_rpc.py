"""
Defines RPC client for the Update Food RPC.
"""

import uuid
from datetime import datetime
from shared import rpcs


class UpdateFoodRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which updates existing
    food items in the user's inventory.
    """
    
    def call(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        auth_user: str,
        srv_from: str,
        food_id: uuid.UUID,
        label: str,
        description: str | None = None,
        api_version="1.0.0",
    ):
        """
        Calls Update Food RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            data={
                "food_id": food_id,
                "label": label,
                "description": description
            },
        )

        return self._call(body=req)
c