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

    def call(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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
            auth_user: str - name of the authenticated
                             user / session token calling.
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

    def check_valid_username_call(
        self,
        auth_user: str,
        srv_from: str,
        username: str,
        api_version="1.0.0",
    ) -> bool:
        """
        Calls the RPC with the check valid
        step. If a username is valid, a valkey
        stage will be created for the auth_user
        with a time to live of 30m stating their
        username is valid. See server docs
        for what "valid" means.

        Args:
            auth_user: str - name of the session token calling.
            srv_from: str - name of the calling service.
            username: str - the username to check.
            api_version="1.0.0" - the API version to call.
        """
        step_data = {
            "step": "check-valid-username",
            "username": username,
        }

        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            step_data,
        )

        return self._call(body=req)
