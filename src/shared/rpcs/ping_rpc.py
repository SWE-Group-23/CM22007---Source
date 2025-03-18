"""
Example implementation of an extremely
simple "ping - pong" RPC client.
"""

from shared import rpcs


class PingRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which just
    sends "Ping!".
    """

    def call(self, service, *args, **kwargs):
        """
        Send "Ping!" to server.
        """
        req = rpcs.request(
            "",
            "1.0.0",
            service,
            data={
                "message": "Ping!"
            }
        )

        return self._call(body=req)
