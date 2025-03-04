"""
Base classes for RPC clients and servers.

RPC naming convention:
    - {rpc_prefix}-resp-q-{UUID} - name of the queue an RPC server should
                                   respond to, declared by the RPC client.
    - {rpc_prefix}-resp-exc - name of the response exchange for the RPC server
                              to send it's response to, declared by k8s yaml
                              in {sub-system}/queues.
    - {rpc_prefix}-call-q - name of the queue to send a call to, declared
                            by k8s yaml in {sub-system}/queues, consumed
                            by an RPC server.
    - {rpc_prefix}-call-exc - name of the exchange to send a call to, declared
                              by k8s yaml in {sub-system}/queues.

rpc_prefix should be consistent across an RPC server and client.

Client definitions should go in the same directory as this file,
as they may be used by multiple different services.

Server definitions should go in the server service's source as only
one service should run an RPC (though k8s replicas of the same service
are fine).
"""

import logging
import uuid
from abc import ABC, abstractmethod

import pika

import shared


class RPCClient(ABC):
    """
    Abstract base class for an RPC client.
    Connects to RabbitMQ, declares a queue to listen
    back on, and creates a consumer for it.

    A sub-class must implement the abstract method
    `call` which specifies what the body of the
    calling message should be.
    """

    def __init__(self, rabbitmq_user, rabbitmq_pass, rpc_prefix):
        """
        Connects to RabbitMQ with provided credentials,
        creates a new queue using the `rpc_prefix` and
        the RPC queue and exchange convention defined in
        the module docstring.
        """
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
            auto_ack=True,
        )

        self.response = None
        self.corr_id = None

    def on_response(self, _ch, _method, props, body):
        """
        Checks if the correlation ID is correct, if it is,
        then populate self.response with the body of the
        message which `_call` waits and blocks on.
        """
        if self.corr_id == props.correlation_id:
            self.response = body

    def _call(self, body):
        """
        Generic implementation of an RPC call, should be
        called by the sub-class' `call` method with the
        correct body for a call.
        """
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
        logging.info("[to %s-call-q, id %s] %s",
                     self.rpc_prefix, self.corr_id, body)
        while self.response is None:
            self.connection.process_data_events(time_limit=1)
        return self.response

    @abstractmethod
    def call(self):
        """
        Should be implemented in sub-classes which
        should call `_call` with the correct body
        for a call.
        """
        raise NotImplementedError


class RPCServer(ABC):
    """
    Abstract base class for an RPC serer.
    Connects to RabbitMQ and creates a consumer on
    it's RPC call queue.

    A sub-class must implement the abstract
    method `process` which should process a request
    and return the response.

    To start an RPC server, you can do (for example):
        rpc_server = PingRPCServer(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        rpc_server.channel.start_consuming()
    """

    def __init__(self, rabbitmq_user, rabbitmq_pass, rpc_prefix):
        """
        Connects to RabbitMQ with provided credentialsa and
        creates a consumer determined by `rpc_prefix` using
        the convention described in the module docstring.
        """
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

    def on_call(self, ch, _method, props, body):
        """
        Generic implementation of an RPC call receiver,
        called whenever a message is received in the
        call queue.
        """
        response = self.process(body)
        ch.basic_publish(
            exchange="ping-rpc-resp-exc",
            routing_key=props.reply_to,
            properties=pika.BasicProperties(
                correlation_id=props.correlation_id),
            body=response,
        )
        logging.info("[to %s, id %s] %s", props.reply_to,
                     props.correlation_id, response)

    @abstractmethod
    def process(self, body):
        """
        Should be implemented in sub-classes which
        should take the body, process the request,
        and then return the response.
        """
        raise NotImplementedError
