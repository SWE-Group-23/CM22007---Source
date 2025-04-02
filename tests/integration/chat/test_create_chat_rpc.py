"""
Integration tests for the create chat RPC.
"""

import os
import json
import logging

from lib import AutocleanTestCase
from shared.rpcs.create_chat_rpc import CreateChatRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class CreateChatRPCTest(AutocleanTestCase):
    """
    Integration tests for the create chat RPC.
    """

    def setUp(self):  # pylint: disable=invalid-name
        """
        Sets up Scylla and RPC Clients.
        """
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.create_chat_client = CreateChatRPCClient(
            os.environ["RABBITMQ_USERNAME"], os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-chat-rpc",
        )

    def test_create_chat(self):
        """
        Tests sending a valid message
        """
        logging.info("Starting the test_send_message test.")
        client = self.create_chat_client

        receiver_user = str("Bob")

        resp_raw = client.call(
            "john smith",
            "testing",
            receiver_user,
        )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Success")

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
