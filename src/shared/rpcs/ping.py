from shared.rpcs import RPCClient


class PingRPCClient(RPCClient):
    def call(self):
        return self._call(body="Ping!")
