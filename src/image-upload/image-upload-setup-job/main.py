"""
Sets up ScyllaDB for the subsystem.
"""

import os


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


if __name__ == "__main__":
    os.environ["CQLENG_ALLOW_SCHEMA_MANAGEMENT"] = "1"
    main()
