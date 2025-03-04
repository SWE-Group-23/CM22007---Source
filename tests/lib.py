import os
from unittest import TestCase

import cassandra.cluster as cc
import cassandra.auth as ca
import cassandra as cs


class AutocleanTestCase(TestCase):
    """
    Test case that automatically cleans:
    - ScyllaDB
    - RabbitMQ
    - Valkey
    """

    def tearDown(self):
        cluster = cc.Cluster(
            contact_points=["dev-db-client.scylla.svc"],
            auth_provider=ca.PlainTextAuthProvider(
                username=os.environ["SCYLLADB_USERNAME"],
                password=os.environ["SCYLLADB_PASSWORD"],
            ),
            load_balancing_policy=cs.policies.TokenAwarePolicy(
                cs.policies.DCAwareRoundRobinPolicy(),
            ),
            protocol_version=4,
        )
        session = cluster.connect()

        # get all keyspace names
        keyspaces_rows = session.execute(
            "SELECT keyspace_name FROM system_schema.keyspaces;"
        )

        # filter out system keyspace
        keyspaces = [
            row.keyspace_name
            for row in keyspaces_rows
            if not row.keyspace_name.startswith("system")
        ]

        # truncate all tables in all keyspaces
        for keyspace in keyspaces:
            # get tables in keyspace
            tables_query = session.prepare(
                """
                SELECT table_name
                FROM system_schema.tables
                WHERE keyspace_name = ?;
                """
            )
            tables = session.execute(tables_query, [keyspace])

            # truncate all tables in keyspace
            for table in tables:
                # print(f"Truncating {keyspace}.{str(table.table_name)}...")
                session.execute(f"TRUNCATE {keyspace}.{table.table_name};")
