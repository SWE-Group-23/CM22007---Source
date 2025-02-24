"""
Example service.
"""

import os
import uuid
import functools
import pika

import shared


def message_callback(scylla_session, ch, method, properties, body):
    """
    The method called when a RabbitMQ message is
    received.

    For example purposes, it just puts the message in a messages
    table with a random UUID.
    """
    # add to db
    print(f"[RECEIVED] {body}")
    message = {
        "id": uuid.uuid4(),
        "message": body.decode(),
    }
    query = scylla_session.prepare(
        """
        INSERT INTO pings (id, message) VALUES (?, ?);
        """
    )
    scylla_session.execute(query, message.values())

    # respond
    ch.basic_publish(
        exchange='ping-rpc-resp-exc',
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id
        ),
        body="Pong!",
    )
    print("[RESPONDED] Pong!")


def main():
    """
    Example main.
    """
    # Set up database session
    # NOTE: non-default creds will be required in the future.
    session = shared.setup_scylla(
        ["dev-db-client.scylla.svc"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # Set keyspace
    session.set_keyspace(os.environ["SCYLLADB_KEYSPACE"])

    # Create table for storing pings
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS pings (
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
    _, channel = shared.setup_rabbitmq(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
    )

    # Configure and start consuming
    channel.basic_consume(
        queue="ping-rpc-call-q",
        on_message_callback=callback,
        auto_ack=True,
    )

    print("[INFO] Consuming...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
