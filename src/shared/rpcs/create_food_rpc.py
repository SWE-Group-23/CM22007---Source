"""
Defines RPC client for the Create Food RPC.
"""

import uuid
from datetime import datetime

from shared import rpcs


class CreateFoodRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which creates food item
    for user's private inventory.
    """

    def call(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        auth_user: str,
        srv_from: str,
        label: str,
        useby: datetime,
        img_id: uuid.UUID | None = None,
        description: str | None = None,
        api_version="1.0.0",
    ) -> bytes:
        """
        Calls Create Food RPC
        """
        data = {
            "label": label,
            "useby": useby.isoformat(timespec="minutes"),
        }

        if img_id is not None:
            data["img_id"] = str(img_id)

        if description is not None:
            data["description"] = description

        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            data=data,
        )

        return self._call(body=req)
