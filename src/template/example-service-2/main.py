"""
Example service.
"""

import os
import time
import cassandra.cqlengine.management as cm

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

    # Create table to store pongs
    cm.sync_table(models.Pongs)

    ping_rpc = PingRPCClient(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
        "ping-rpc",
    )

    while True:
        print("CALLING")
        response = ping_rpc.call()
        print(f"[RECEIVED] {response}")
        models.Pongs.create(message=response.decode())
        time.sleep(1)


if __name__ == "__main__":
    os.environ["CQLENG_ALLOW_SCHEMA_MANAGEMENT"] = "1"
    main()
