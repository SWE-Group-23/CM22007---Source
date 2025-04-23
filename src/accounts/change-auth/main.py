"""
Handles changing a users authentication factors given at least two correct
factors.
"""

import os
import logging

import shared
from shared import rpcs
from shared.models import accounts as model

import valkey
import argon2
import pyotp


class ChangeAuthRPCServer(rpcs.RPCServer):
    """
    Serves the change auth RPC.
    """

    def __init__(
        self,
        rabbitmq_user: str,
        rabbitmq_pass: str,
        vk: valkey.Valkey,
        *,
        rpc_prefix="change-auth-rpc",
    ):
        self.vk = vk
        self.ph = argon2.PasswordHasher()
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def process(self, body: bytes) -> str:
        raise NotImplementedError


def main():
    """
    Connect to ScyllaDB, Valkey, and start running the RPC server.
    """
    logging.info("Connecting to ScyllaDB...")
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    logging.info("Connecting to Valkey...")
    vk = valkey.Valkey(
        host="accounts-valkey",
        port="6379",
        db=0,
        username=os.environ["VALKEY_USERNAME"],
        password=os.environ["VALKEY_PASSWORD"],
    )

    logging.info("Setting up RPC server...")
    rpc_server = ChangeAuthRPCServer(
        vk=vk,
        rabbitmq_user=os.environ["RABBITMQ_USERNAME"],
        rabbitmq_pass=os.environ["RABBITMQ_PASSWORD"],
    )

    logging.info("Consuming...")
    rpc_server.channel.start_consuming()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
