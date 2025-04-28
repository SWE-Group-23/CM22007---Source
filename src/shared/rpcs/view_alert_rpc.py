"""
The rpc for viewing an alert.
"""


from shared import rpcs


class ViewAlertRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which views the alert.
    """
    def __init__(self, *args, rpc_prefix="view-alert-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call( # pylint: disable=too-many-arguments,too-many-positional-arguments
            self,
            auth_user: str,
            service: str,
            version="1.0.0"):
        """
        Send the JSON to the server.
        """
        data = {}
        req = rpcs.request(
                auth_user,
                version,
                service,
                data)

        return self._call(body=req)
