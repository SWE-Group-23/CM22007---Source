"""
Client for using the login RPC from the
accounts subsystem.
"""

import json

from shared import rpcs


class LoginRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the login RPC
    from the accounts subsystem.
    """

    def __init__(self, *args, rpc_prefix="login-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        sid: str,
        srv_from: str,
        step: str,
        step_data: dict,
        api_version="1.0.0",
    ) -> bytes:
        """
        Calls the login RPC.

        Args:
            sid: str - session ID calling.
            srv_from: str - name of the calling service.
            step: str - the step through the login
                        process.
            step_data: dict - the data used for the step
                              in the login process.
            api_version="1.0.0" - the API version to call.

        Returns:
            bytes - the raw response from the RPC server.
        """
        step_data["step"] = step
        req = rpcs.request_unauth(
            sid,
            api_version,
            srv_from,
            step_data,
        )

        return self._call(body=req)

    def user_pw_call(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        sid: str,
        srv_from: str,
        username: str,
        password_digest: str,
        api_version="1.0.0",
    ) -> dict:
        """
        Calls the username-password stage of
        the login RPC.

        Args:
            sid: str - session ID calling.
            srv_from: str - name of the calling service.
            username: str - username of the account.
            password_digest: str - the digest of the password
                                   from the gateway.
            api_version="1.0.0" - the API version to call.

        Returns:
            dict - deserialised JSON response from the server.

        Could throw a json.JSONDecodeError.
        """

        step_data = {
            "step": "username-password",
            "username": username,
            "password_digest": password_digest,
        }

        req = rpcs.request_unauth(
            sid,
            api_version,
            srv_from,
            step_data,
        )

        return json.loads(self._call(body=req))

    def verify_otp_call(
        self,
        sid: str,
        srv_from: str,
        otp: str | int,
        api_version="1.0.0",
    ) -> dict:
        """
        Calls the verify OTP stage of the login RPC.

        Args:
            sid: str - session ID calling.
            srv_from: str - name of the calling service.
            otp: str | int - the OTP to verify.
            api_version="1.0.0" - the API version to call.

        Returns:
            dict - deserialised JSON response from the server.

        Could throw a json.JSONDecodeError.
        """

        step_data = {
            "step": "verify-otp",
            "otp": otp,
        }

        req = rpcs.request_unauth(
            sid,
            api_version,
            srv_from,
            step_data,
        )

        return json.loads(self._call(body=req))
