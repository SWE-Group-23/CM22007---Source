"""
Example service.
"""

import os

import valkey

import shared
from shared import rpcs
from shared.models import template as models


class PingRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which
    simply returns "Pong!" no matter
    what.
    """

    def process(self, body):
        """
        Respond with "Pong!", unless message
        isn't "Ping!".
        """
        print(f"[RECEIVED] {body.decode()}")
        models.Pings.create(message=body.decode())

        if body.decode() == "Ping!":
            print("[RESPONDING] Pong!")
            return "Pong!"

        print("[RESPONDING] That's not a ping!")
        return "That's not a ping!"


def main():
    """
    Example main.
    """
    # Set up database session
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    r = valkey.Valkey(
        host="valkey-example",
        port="6379",
        db=0,
        username=os.environ["VALKEY_USERNAME"],
        password=os.environ["VALKEY_PASSWORD"],
    )
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
