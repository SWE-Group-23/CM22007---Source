import cassandra.cluster as cc
import cassandra.auth as ca
import pika


def setup_rabbitmq(
    user: str,
    password: str,
    *,
    host="rabbitmq"
) -> pika.channel.Channel:
    """
    Sets up a connection to RabbitMQ, returning
    a channel.

    Args;
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

    return connection.channel()


def setup_scylla(
    contact_points: list[str],
    *,
    user="cassandra",
    password="cassandra",
) -> cc.Session:
    """
    Creates a cassandra.cluster.Session with
    given information.

    Args:
        contact_points: list[str] -- hostnames of Scylla clients to connect to.
        user: str -- username to use when connecting to database.
        password: str -- password to use when connecting to database.

    Returns:
        cassandra.cluster.Session -- the session created from the
                                     connection to the Scylla cluster
    """
    cluster = cc.Cluster(
        contact_points=contact_points,
        auth_provider=ca.PlainTextAuthProvider(
            username=user,
            password=password,
        )
    )

    return cluster.connect()
