"""
Example service.
"""

import os
import time
import pika
import uuid

import shared


class PingRPCClient(object):
    def __init__(self):
        self.connection, self.channel = shared.setup_rabbitmq(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
        )

        result = self.channel.queue_declare(
            queue=f'ping-rpc-resp-q-{uuid.uuid4()}', exclusive=True
        )
        self.channel.queue_bind(result.method.queue, 'ping-rpc-resp-exc')
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

        self.response = None
        self.corr_id = None

    def on_response(self, _ch, _method, properties, body):
        if self.corr_id == properties.correlation_id:
            self.response = body

    def call(self):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="ping-rpc-call-exc",
            routing_key="ping-rpc-call-q",
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body="Ping!",
        )
        print("[SENT] Ping!")
        while self.response is None:
            self.connection.process_data_events(
                time_limit=1
            )
        return self.response


def main():
    """
    Example main.
    """

    session = shared.setup_scylla(
        ["dev-db-client.scylla.svc"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # Set keyspace
    session.set_keyspace(os.environ["SCYLLADB_KEYSPACE"])

    # Create table to store pongs
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS pongs (
            id UUID PRIMARY KEY,
            message text,
        )
        """
    )

    ping_rpc = PingRPCClient()
    while True:
        response = ping_rpc.call()
        print(f"[RECEIVED] {response}")
        message = {
            "id": uuid.uuid4(),
            "message": response.decode(),
        }
        query = session.prepare(
            """
            INSERT INTO pongs (id, message) VALUES (?, ?);
            """
        )
        session.execute(query, message.values())
        time.sleep(1)


if __name__ == "__main__":
    main()
