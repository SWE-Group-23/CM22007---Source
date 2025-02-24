"""
Classes for RPC clients and servers
"""

import uuid
from abc import ABC, abstractmethod

import shared
import pika


class RPCClient(ABC):
    def __init__(self, rabbitmq_user, rabbitmq_pass, rpc_prefix):
        self.rpc_prefix = rpc_prefix
        self.connection, self.channel = shared.setup_rabbitmq(
            rabbitmq_user,
            rabbitmq_pass,
        )

        result = self.channel.queue_declare(
            queue=f"{rpc_prefix}-resp-q-{uuid.uuid4()}", exclusive=True
        )
        self.channel.queue_bind(result.method.queue, f"{rpc_prefix}-resp-exc")
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

        self.response = None
        self.corr_id = None

    def on_response(self, _ch, _method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def _call(self, body):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange=f"{self.rpc_prefix}-call-exc",
            routing_key=f"{self.rpc_prefix}-call-q",
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=body,
        )
        print(f"[to {self.rpc_prefix}-call-q, id {self.corr_id}] {body}")
        while self.response is None:
            self.connection.process_data_events(
                time_limit=1
            )
        return self.response

    @abstractmethod
    def call(*args, **kwargs):
        raise NotImplementedError


class RPCServer(ABC):
    def __init__(self, rabbitmq_user, rabbitmq_pass, rpc_prefix):
        self.rpc_prefix = rpc_prefix
        self.connection, self.channel = shared.setup_rabbitmq(
            rabbitmq_user,
            rabbitmq_pass,
        )

        self.channel.basic_consume(
            queue=f"{rpc_prefix}-call-q",
            on_message_callback=self.on_call,
            auto_ack=True,
        )

    def on_call(self, ch, method, props, body):
        response = self.process(body)
        ch.basic_publish(
            exchange='ping-rpc-resp-exc',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id
            ),
            body=response,
        )
        print(f"[to {props.reply_to}, id {props.correlation_id}] {response}")

    @abstractmethod
    def process(body, *args, **kwargs):
        raise NotImplementedError
