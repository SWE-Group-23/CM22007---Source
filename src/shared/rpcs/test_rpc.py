"""
Defines an RPC client that allows you to send anything for
use in integration testing.
"""

from shared.rpcs import RPCClient


class TestRPCClient(RPCClient):
    """
    Used for integration testing RPC calls.
    """

    def call(self, body):  # pylint: disable=arguments-differ
        """
        Calls the specified RPC with the given
        body.
        """
        return self._call(body)
