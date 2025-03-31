"""Creates RPC Client for create account service."""
from shared import rpcs

class CreateProfileRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the create profile RPC
    from the profile subsystem.
    """

    def __init__(self, *args, rpc_prefix="create-profile-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call( # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        auth_user: str,
        srv_from: str,
        username: str,
        name: str,
        bio: str,
        food_preferences: str,
        api_version="1.0.0",
    ) -> dict:
        """
        sends data for profile set up
        """

        data = {
            "username": username,
            "name": name,
            "bio": bio,
            "food_preferences": food_preferences
        }

        req = rpcs.request(
            auth_user,
            api_version,
            srv_from,
            data,
        )

        return self._call(body=req)
