"""
Example service.
"""

import os
import time

import shared


def main():
    """
    Example main.
    """

    env = os.environ

    channel = shared.setup_rabbitmq(
        env["RABBITMQ_USERNAME"],
        env["RABBITMQ_PASSWORD"],
    )

    while True:
        channel.basic_publish(
            exchange='template-exchange',
            routing_key='template-queue',
            body="Hello, RabbitMQ!"
        )
        print("[SENT] Hello, RabbitMQ!")
        time.sleep(10)


if __name__ == "__main__":
    main()
