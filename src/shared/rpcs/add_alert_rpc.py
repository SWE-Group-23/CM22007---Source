"""
The rpc for adding an alert.
"""


from shared.rpcs import RPCClient


class PingRPCClient(RPCClient):
    """
    Sub-class of RPC client which sends adds the alert.
    """

    def call(self, sid, version="1.0.0", from_svc, data):
        """
        Send the JSON to the server.
        """
	request = rpcs.request_unauth(sid,version,from_svc,data)
        return self._call(body=request)


)

