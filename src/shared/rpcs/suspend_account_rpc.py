"""
RPC Client for the Suspend Account service in
the accounts subsystem.
"""

import json
from datetime import datetime as dt

from shared import rpcs


class SuspendAccountRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the login RPC
    from the accounts subsystem.
    """

    def __init__(self, *args, rpc_prefix="suspend-account-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        auth_mod: str,
        srv_from: str,
        username: str,
        suspend_until: str,
        suspend_from=str(dt.now()),
        api_version="1.0.0",
    ) -> dict:
        """
        Calls the suspend account RPC.

        Args:
            auth_mod: str - the authenticated moderator
                            making the call.
            srv_from: str - name of the calling service.
            username: str - the username to suspend.
            suspend_until: str - the datetime string to suspend the
                                 user until.
            suspend_from=str(dt.now()) - the datetime string to
                                         suspend the user from.
            api_version="1.0.0" - the API version to call.

        Returns:
            dict - the parsed JSON response from the RPC server.

        Could cause a JSONDecodeError.
        """
        req = rpcs.request_moderation(
            auth_mod,
            api_version,
            srv_from,
            {
                "username": username,
                "suspend_from": suspend_from,
                "suspend_until": suspend_until,
            },
        )

        return json.loads(self._call(body=req))
