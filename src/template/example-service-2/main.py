"""
Example service.
"""

import os
import time

import pika


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

    while True:
        channel.basic_publish(
            exchange='example-services-exchange',
            routing_key='example-services-queue',
            body="Hello, RabbitMQ!"
        )
        print("[SENT] Hello, RabbitMQ!")
        time.sleep(10)


if __name__ == "__main__":
    main()
