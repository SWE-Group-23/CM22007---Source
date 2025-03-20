from shared import rpcs
import uuid
import datetime

class CreateFoodRPCClient(rpcs.RPCClient):
    """
    Sub-class of RPC client which creates food item
    for user's private inventory.
    """

    def call(self, *args, **kwargs):
        return super().call(*args, **kwargs)
        