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
            env_vars["RABBITMQ_SERVICE_HOST"],
            credentials=credentials
        )
    )

    _ = connection.channel()

    time.sleep(120)

    print("Hello from example-service 1")


if __name__ == "__main__":
    main()
