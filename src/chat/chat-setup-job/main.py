"""
Sets up ScyllaDB for the subsystem.
"""

import os

import cassandra.cqlengine.management as cm

import shared
from shared.models import template as models


def main():
    """
    Connects to Scylla then ensures table schemas
    are correct.
    """
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )
    
    # sync tables here
    print("Setting up chats table...")
    cm.sync_table(models.Chats)
    print("Setting up messages table...")
    cm.sync_table(models.Messages)


if __name__ == "__main__":
    os.environ["CQLENG_ALLOW_SCHEMA_MANAGEMENT"] = "1"
    main()
