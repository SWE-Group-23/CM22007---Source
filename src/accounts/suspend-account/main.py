"""
Service that allows moderators to suspend an account.
"""

import os
import json
import logging
from datetime import datetime as dt

from cassandra.cqlengine.query import DoesNotExist

import shared
from shared import rpcs
from shared.models import accounts as model


class SuspendAccountRPCServer(rpcs.RPCServer):
    """
    The RPC server for the Suspend Account RPC.

    Expects requests to have authMod instead of
    authUser, as it is a moderation service.
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        *,
        rpc_prefix="suspend-account-rpc",
    ):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def process(self, body: bytes) -> str:
        """
        Processes a suspension request.

        Dates must be in the form "%Y-%m-%d %H:%M:%S.%f",
        this is the default for str(datetime.datetime.now()).
        """
        logging.info("[RECEIVED]")

        # decode json
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Bad JSON."})

        try:
            # check version
            if req["version"] != "1.0.0":
                return rpcs.response(400, {"reason": "Bad version."})

            # TODO: check a moderator is who they say they are or just blindly
            # trust the gateway?
            if req["authMod"] is None or req["authMod"] == "":
                return rpcs.response(400, {"reason": "Malformed request."})

            start = dt.strptime(
                req["data"]["suspend_from"],
                "%Y-%m-%d %H:%M:%S.%f",
            )

            end = dt.strptime(
                req["data"]["suspend_until"],
                "%Y-%m-%d %H:%M:%S.%f",
            )

            if start > end:
                return rpcs.response(
                    400,
                    {"reason": "Start time must be before end time."},
                )

            sus = model.Suspension(
                start=start,
                end=end,
                suspended_by=req["authMod"],
            )

            try:
                user = model.Accounts.get(
                    username=req["data"]["username"],
                )
            except DoesNotExist:
                return rpcs.response(400, {"reason": "User does not exist."})

            user.suspension_history.append(sus)
            user.save()

            return rpcs.response(200, {"success": True})

        except (KeyError, ValueError):
            return rpcs.response(400, {"reason": "Malformed request."})


def main():
    """
    Sets up the ScyllaDB connection and starts
    serving the RPC.
    """
    logging.info("Connecting to ScyllaDB...")
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    logging.info("Setting up RPC server...")
    rpc_server = SuspendAccountRPCServer(
        rabbitmq_user=os.environ["RABBITMQ_USERNAME"],
        rabbitmq_pass=os.environ["RABBITMQ_PASSWORD"],
    )

    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
