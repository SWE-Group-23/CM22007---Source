"""
Example service.
"""

import os
import uuid
import functools

import shared


def message_callback(scylla_session, _ch, _method, _properties, body):
    """
    The method called when a RabbitMQ message is
    received.

    For example purposes, it just puts the message in a messages
    table with a random UUID.
    """

    print(f"[RECEIVED] {body}")
    message = {
        "id": uuid.uuid4(),
        "message": body.decode(),
    }
    query = scylla_session.prepare(
        """
        INSERT INTO messages (id, message) VALUES (?, ?);
        """
    )
    scylla_session.execute(query, message.values())


def main():
    """
    Example main.
    """

    env_vars = os.environ

    # Set up database session
    # NOTE: non-default creds will be required in the future.
    session = shared.setup_scylla(
        ["example-db-client.scylla.svc"],
    )

    # Create a keyspace for the service
    # NOTE: this will be done by the CRD
    session.execute(
        """
        CREATE KEYSPACE IF NOT EXISTS example_service
            WITH REPLICATION = {
                'class': 'SimpleStrategy',
                'replication_factor': '3'
            }
            AND DURABLE_WRITES = true;
        """
    )

    # Use that keyspace
    session.set_keyspace("example_service")

    # Create table for stuff
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id UUID PRIMARY KEY,
            message text,
        )
        """
    )

    # Create a callback handler with the Scylla session
    callback = functools.partial(
        message_callback,
        session,
    )

    # Create RabbitMQ channel
    channel = shared.setup_rabbitmq(
        env_vars["RABBITMQ_USERNAME"],
        env_vars["RABBITMQ_PASSWORD"],
    )

    # Configure and start consuming
    channel.basic_consume(
        queue="example-services-queue",
        on_message_callback=callback,
        auto_ack=True,
    )

    print("[INFO] Consuming...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
