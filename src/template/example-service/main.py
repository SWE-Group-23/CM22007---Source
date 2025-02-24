"""
Example service.
"""

import os

import shared
import shared.rpcs as rpcs


class PingRPCServer(rpcs.RPCServer):
    def process(self, _body):
        return "Pong!"


def main():
    """
    Example main.
    """
    # Set up database session
    # NOTE: non-default creds will be required in the future.
    session = shared.setup_scylla(
        ["dev-db-client.scylla.svc"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # Set keyspace
    session.set_keyspace(os.environ["SCYLLADB_KEYSPACE"])

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
