"""
Client for using the register RPC from the
accounts subsystem.
"""

from shared import rpcs


class RegisterRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the register RPC
    from the accounts subsystem.
    """

    def call(
        self,
        auth_user: str,
        srv_from: str,
        step: str,
        step_data: dict,
        api_version="1.0.0",
    ) -> bytes:
        """
        Calls the register RPC.

        Args:
            srv_from: str - name of the calling service.
            step: str - the step through the registration
                        process.
            step_data: dict - the data used for the step
                              in the registration process.
            api_version="1.0.0" - the API version to call.

        Returns:
            bytes - the raw response from the RPC server.
        """
        step_data["step"] = step
        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            step_data,
        )

        return self._call(body=req)
