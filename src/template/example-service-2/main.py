"""
Example service.
"""

import os
import logging
import json
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
        logging.info("[CALLING]")
        resp_raw = ping_rpc.call("example-service-2")

        logging.info(f"[RECEIVED] {resp_raw}")
        try:
            resp = json.loads(resp_raw)
            models.Pongs.create(message=resp["data"]["message"])
        except json.JSONDecodeError:
            logging.warning("[BAD RESPONSE] Couldn't decode JSON.")
        except KeyError:
            logging.warning("[BAD RESPONSE] Response not formatted correctly.")

        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
