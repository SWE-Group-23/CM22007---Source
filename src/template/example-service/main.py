"""
Example service.
"""

import os

import pika


def message_callback(ch, method, properties, body):
    print(f"[RECEIVED] {body}")


def main():
    """
    Example main.
    """

    env_vars = os.environ

    credentials = pika.PlainCredentials(
            env_vars["RABBITMQ_USERNAME"],
            env_vars["RABBITMQ_PASSWORD"],
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            "rabbitmq",
            credentials=credentials
        )
    )

    channel = connection.channel()

    channel.queue_declare(queue="hello-rabbitmq")

    channel.basic_consume(
        queue="hello-rabbitmq",
        on_message_callback=message_callback,
        auto_ack=True,
    )

    print("[INFO] Consuming...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
