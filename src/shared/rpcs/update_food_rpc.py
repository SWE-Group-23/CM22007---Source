"""
Defines RPC client for Update Food RPC.
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
        service: str,
        api_version="1.0.0",
    ):
        """
        Calls Update Food RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data={
                # data to be sent
            },
        )

        return self._call(body=req)
