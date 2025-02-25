"""
Example service.
"""

import os
import time
import uuid

import shared
from shared.rpcs.ping import PingRPCClient


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

    # Create table to store pongs
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS pongs (
            id UUID PRIMARY KEY,
            message text,
        )
        """
    )

    ping_rpc = PingRPCClient(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
        "ping-rpc",
    )

    while True:
        response = ping_rpc.call()
        print(f"[RECEIVED] {response}")
        message = {
            "id": uuid.uuid4(),
            "message": response.decode(),
        }
        query = session.prepare(
            """
            INSERT INTO pongs (id, message) VALUES (?, ?);
            """
        )
        session.execute(query, message.values())
        time.sleep(1)


if __name__ == "__main__":
    main()
