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

    env_vars = os.environ

    channel = shared.setup_rabbitmq(
        env_vars["RABBITMQ_USERNAME"],
        env_vars["RABBITMQ_PASSWORD"],
    )

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
