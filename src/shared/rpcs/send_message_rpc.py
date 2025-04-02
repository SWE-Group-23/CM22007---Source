"""
Client for using the send message RPC from the
chat subsystem.
"""

from shared import rpcs


class SendMessageRPCClient(rpcs.RPCClient):
    """
    RPC Client for using the send message RPC from the
    chat subsystem.
    """

    def __init__(self, *args, rpc_prefix="send-message-rpc", **kwargs):
        super().__init__(*args, rpc_prefix, **kwargs)

    def call(   # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        auth_user: str,
        service: str,
        chat_id,
        receiver_user: str,
        time_sent: str,
        message: str,
        api_version="1.0.0"):
        """
        Calls send message RPC
        """
        req = rpcs.request(
            auth_user,
            api_version,
            service,
            data={
                "chat_id": str(chat_id),
                "receiver_user": receiver_user,
                "time_sent": time_sent,
                "message": message,
            },
        )

        return self._call(body=req)
