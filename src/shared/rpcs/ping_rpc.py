"""
Example implementation of an extremely
simple "ping - pong" RPC client.
"""


from shared.rpcs import RPCClient


class PingRPCClient(RPCClient):
    """
    Sub-class of RPC client which just
    sends "Ping!".
    """

    def call(self):
        """
        Send "Ping!" to server.
        """
        return self._call(body="Ping!")
