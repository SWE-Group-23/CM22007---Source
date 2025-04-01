"""
Integration tests for the send message RPC.
"""

import os
import uuid
import time
import json
import logging

from lib import AutocleanTestCase
from shared.rpcs.send_message_rpc import SendMessageRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class SendMessageRPCTest(AutocleanTestCase):
    """
    Integration tests for the send message RPC.
    """

    def setUp(self):    # pylint: disable=invalid-name
        """
        Sets up Scylla and RPC Clients.
        """
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.send_message_client = SendMessageRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "send-message-rpc",
        )


    def test_send_message(self):
        """
        Tests sending a valid message
        """
        logging.info("Starting the test_send_message test.")
        client = self.send_message_client

        chat_id = uuid.uuid4()
        sender_user = str(uuid.uuid4())
        receiver_user = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        message = "test message"

        resp_raw = client.call(
            "john smith",
            "testing",
            chat_id,
            sender_user,
            receiver_user,
            timestamp,
            message
            )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Message sent")

    def test_send_new_chat_message(self):
        """
        Tests sending a message to a new chat
        """
        logging.info("Starting the test_send_new_chat_message test.")
        client = self.send_message_client

        chat_id = "None"
        sender_user = str(uuid.uuid4())
        receiver_user = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        message = "New chat test message"

        resp_raw = client.call(
            "john smith",
            "testing",
            chat_id,
            sender_user,
            receiver_user,
            timestamp,
            message
            )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Message sent")

    def test_send_nothing(self):
        """
        Tests sending a poorly formed message request
        """
        client = self.test_client

        resp_raw = client.call("")
        response = json.loads(resp_raw)

        logging.info("Response: %s", response)
        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["reason"], "Bad JSON.")
