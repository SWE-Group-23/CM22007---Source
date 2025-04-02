"""
The rpc for adding an alert.
"""


from shared import rpcs


class AddAlertRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which sends adds the alert.
    """
    def __init__(self, *args, rpc_prefix="add-alert-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call( # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            auth_user: str,
            service: str,
            message: str,
            version="1.0.0"):
        """
        Send the JSON to the server.
        """
        req = rpcs.request(
                auth_user,
                version,
                service,
                data = {
                   "message": message
                }
        )

        return self._call(body=req)
