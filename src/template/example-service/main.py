"""
Example service.
"""

import os

import shared
from shared import rpcs

import valkey


class PingRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which
    simply returns "Pong!" no matter
    what.
    """

    def process(self, body, *args, **kwargs):
        """
        Respond with "Pong!", unless message
        isn't "Ping!".
        """
        if body.decode() == "Ping!":
            return "Pong!"
        return "That's not a ping!"


def main():
    """
    Example main.
    """
    # Set up database session
    session = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    r = valkey.Valkey(host="valkey-example", port="6379", db=0, username="default", password=os.environ["VALKEY_PASSWORD"])
    r.set("test", "success")
    print(f"response: {r.get('test')}")

    # Create table for storing pings
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS pings (
            id UUID PRIMARY KEY,
            message text,
        )
        """
    )

    rpc_server = PingRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
        "ping-rpc",
    )

    print("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    main()
