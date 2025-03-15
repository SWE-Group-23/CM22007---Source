"""
Client for using the register RPC from the
accounts subsystem.
"""

import json

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
    ) -> dict:
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

        Returns:
            dict - deserialised JSON response from the server.

        Could throw a json.JSONDecodeError.
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

        return json.loads(self._call(body=req))

    def set_password_call(
        self,
        auth_user: str,
        srv_from: str,
        password_digest: str,
        api_version="1.0.0",
    ) -> dict:
        """
        Calls the RPC with the set password
        step. If the token is at the correct stage
        in Valkey, then the password will be
        added to the token's Valkey stage
        and the step will be updated.

        Args:
            auth_user: str - name of the session token calling.
            srv_from: str - name of the calling service,
            username: str - the username to check.
            api_version="1.0.0" - the API version to call.

        Returns:
            dict - deserialised JSON response from the server.

        Could throw a json.JSONDecodeError.
        """
        step_data = {
            "step": "set-password",
            "password-digest": password_digest,
        }

        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            step_data,
        )

        return json.loads(self._call(body=req))

    def setup_otp_call(
        self,
        auth_user: str,
        srv_from: str,
        api_version="1.0.0",
    ) -> dict:
        """
        Calls the RPC with the setup OTP step.
        If the token is at the correct step in
        Valkey, then the OTP secret will be added
        to the token's Valkey stage and the step
        will be updated.

        Args:
            auth_user: str - name of the session token calling.
            srv_from: str - name of the calling service.
            api_version="1.0.0" - the API version to call.

        Returns:
            dict - deserialised JSON response from the server.

        Could throw a json.JSONDecodeError.
        """
        step_data = {
            "step": "setup-otp",
        }

        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            step_data,
        )

        return json.loads(self._call(body=req))

    def verify_otp_call(
        self,
        auth_user: str,
        srv_from: str,
        otp: str,
        api_version="1.0.0",
    ) -> dict:
        """
        Calls the RPC with the verify OTP step.
        If the token is at the correct step in
        Valkey, then the given OTP will be
        verified against the stored TOTP and
        the token's step will be updated.

        Args:
            auth_user: str - name of the session token calling.
            srv_from: str - name of the calling service.
            otp: str - the OTP to verify.
            api_version="1.0.0" - the API version to call.

        Returns:
            dict - deserialised JSON response from the server.

        Could throw a json.JSONDecodeError.
        """
        step_data = {
            "step": "verify-otp",
            "otp": otp,
        }

        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            step_data,
        )

        return json.loads(self._call(body=req))

    def backup_code_call(
        self,
        auth_user: str,
        srv_from: str,
        api_version="1.0.0",
    ) -> dict:
        """
        Calls the RPC with the backup code step.
        If the token is at the correct step in Valkey,
        the user will be added to the database,
        removed from Valkey, and given a backup
        code.

        Args:
            auth_user: str - name of the session token calling.
            srv_from: str - name of the calling service.
            api_version="1.0.0" - the API version to call.

        Returns:
            dict - deserialised JSON response from the server.

        Could throw a json.JSONDecodeError.
        """
        step_data = {
            "step": "backup-code"
        }

        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            step_data,
        )

        return json.loads(self._call(body=req))
