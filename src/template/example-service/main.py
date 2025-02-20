"""
Example service.
"""

import os
import uuid
import functools
import base64 as b64

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

    env = os.environ

    # Set up database session
    # NOTE: non-default creds will be required in the future.
    session = shared.setup_scylla(
        ["example-db-client.scylla.svc"],
        user=env["SCYLLADB_USERNAME"],
        password=env["SCYLLADB_PASSWORD"],
    )

    # Get keyspace name
    # TODO: move this to shared library.
    keyspace = "k" + b64.b32hexencode(
        "template-keyspace".encode()
    ).decode().replace("=", "_").lower()

    # Use that keyspace
    session.set_keyspace(keyspace)

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
        env["RABBITMQ_USERNAME"],
        env["RABBITMQ_PASSWORD"],
    )

    # Configure and start consuming
    channel.basic_consume(
        queue="template-queue",
        on_message_callback=callback,
        auto_ack=True,
    )

    print("[INFO] Consuming...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
