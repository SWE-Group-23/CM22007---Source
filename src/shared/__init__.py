"""
The shared library for all services to use.
Used to abstract away boilerplate.

Provides:
    setup_rabbitmq -- setup a RabbitMQ channel with given args.
    setup_scylla -- setup a ScyllaDB session with given args.
"""

import cassandra.cluster as cc
import cassandra.auth as ca
import cassandra as cs
import pika


def setup_rabbitmq(
    user: str,
    password: str,
    *,
    host="rabbitmq.rabbitmq.svc.cluster.local"
) -> tuple[pika.BlockingConnection, pika.channel.Channel]:
    """
    Sets up a connection to RabbitMQ, returning
    a channel.

    Args:
        user: str -- username for RabbitMQ connection.
        password: str -- password for RabbitMQ connection.
        host: str -- host of RabbitMQ service (default "rabbitmq")

    Returns:
        pika.channel.Channel -- the channel created from the connection
                                with the host
    """
    credentials = pika.PlainCredentials(
        user,
        password,
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host,
            credentials=credentials,
        )
    )

    return (connection, connection.channel())


def setup_scylla(
    keyspace: str,
    *,
    contact_points=None,
    user="cassandra",
    password="cassandra",
) -> cc.Session:
    """
    Creates a cassandra.cluster.Session with
    given information, setting it's keyspace.

    Args:
        keyspace: str -- the keyspace to set the session to use.
        contact_points: list[str] -- hostnames of Scylla clients to connect to.
        user: str -- username to use when connecting to database.
        password: str -- password to use when connecting to database.

    Returns:
        cassandra.cluster.Session -- the session created from the
                                     connection to the Scylla cluster
    """
    if contact_points is None:
        contact_points = ["dev-db-client.scylla.svc"]

    cluster = cc.Cluster(
        contact_points=contact_points,
        auth_provider=ca.PlainTextAuthProvider(
            username=user,
            password=password,
        ),
        load_balancing_policy=cs.policies.TokenAwarePolicy(
            cs.policies.DCAwareRoundRobinPolicy(),
        ),
        protocol_version=4,
    )

    session = cluster.connect()
    session.set_keyspace(keyspace)

    return session
