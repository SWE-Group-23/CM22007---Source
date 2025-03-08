"""
Internal testing library that provides useful specific
testing classes.
"""

import json
import os
from unittest import TestCase

import cassandra as cs
import cassandra.auth as ca
import cassandra.cluster as cc
import pika
import requests


class AutocleanTestCase(TestCase):
    """
    Test case that automatically cleans:
    - ScyllaDB
    - RabbitMQ
    - Valkey
    """

    def _tear_down_scylla(self):
        """
        Truncates all non-system tables.
        """
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

    def _tear_down_rabbitmq(self):
        """
        Purges all non-exclusive queues.
        """
        # tear down rabbitmq
        # get queues from rabbitmq http api
        user = os.environ["RABBITMQ_USERNAME"]
        password = os.environ["RABBITMQ_PASSWORD"]

        result = requests.get(
            "http://rabbitmq-nodes.rabbitmq.svc:15672/api/queues",
            auth=(user, password),
            timeout=10,
        )

        # get non-exclusive queue names
        queues = filter(
            lambda x: not x["exclusive"],
            list(json.loads(result.content.decode())),
        )

        queue_names = [q["name"] for q in queues]

        # create channel
        credentials = pika.PlainCredentials(
            user,
            password,
        )

        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                "rabbitmq.rabbitmq.svc.cluster.local",
                credentials=credentials,
            )
        )

        channel = connection.channel()

        # purge queues
        for name in queue_names:
            try:
                channel.queue_purge(name)
            except pika.exceptions.ChannelClosedByBroker:
                pass

    def tearDown(self):
        self._tear_down_scylla()
        self._tear_down_rabbitmq()
