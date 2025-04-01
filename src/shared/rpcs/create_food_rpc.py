"""
Defines RPC client for Create Food RPC.
"""

import uuid
from datetime import datetime
from shared import rpcs


class CreateFoodRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which creates food item
    for user's private inventory.
    """

    def call(   # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            auth_user: str,
            service: str,
            food_id: uuid,
            img_id: uuid,
            label: str,
            useby: datetime,
            api_version="1.0.0"):
        """
        Calls Create Food RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data = {
                "food_id": str(food_id),
                "img_id": str(img_id),
                "label": label,
                "useby": useby.isoformat(timespec="minutes")
            }
        )

        return self._call(body=req)
