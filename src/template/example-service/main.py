"""
Example service.
"""

import json
import os
import logging

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
        logging.info("[RECEIVED] %s", body.decode())

        # check json parses
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(
                400,
                {"reason": "Bad JSON."},
            )

        # parse message
        try:
            # version checking
            if req["version"] != "1.0.0":
                return rpcs.response(
                    400,
                    {"reason": "Bad version."}
                )

            message = req["data"]["message"]
            models.Pings.create(
                message=message,
            )

            if message == "Ping!":
                return rpcs.response(
                    200,
                    {"message": "Pong!"}
                )

            return rpcs.response(
                400,
                {"message": "That's not a ping!"}
            )

        # if any keys don't exist then request is malformed
        except KeyError:
            return rpcs.response(
                400,
                {"reason": "Malformed request."}
            )


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

    rpc_server = PingRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
        "ping-rpc",
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
