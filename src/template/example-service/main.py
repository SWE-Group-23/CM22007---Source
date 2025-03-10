"""
Example service.
"""

import os

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

    rpc_server = PingRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
        "ping-rpc",
    )

    print("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    main()
