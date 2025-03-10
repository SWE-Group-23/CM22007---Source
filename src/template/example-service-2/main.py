"""
Example service.
"""

import os
import time

import shared
from shared.rpcs.ping_rpc import PingRPCClient
from shared.models import template as models


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

    ping_rpc = PingRPCClient(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
        "ping-rpc",
    )

    while True:
        print("[CALLING]")
        response = ping_rpc.call()
        print(f"[RECEIVED] {response}")
        models.Pongs.create(message=response.decode())
        time.sleep(1)


if __name__ == "__main__":
    main()
