"""
Integration tests for the delete message RPC.
"""

import os
import uuid
import json
import logging

from lib import AutocleanTestCase
from shared.rpcs.delete_message_rpc import DeleteMessageRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class DeleteMessageRPCTest(AutocleanTestCase):
    """
    Integration tests for the delete message RPC.
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

        self.delete_message_client = DeleteMessageRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "delete-message-rpc",
        )


    def test_delete_message(self):
        """
        Tests sending a valid json to delete message
        """
        logging.info("Starting the test_delete_message test.")
        client = self.delete_message_client

        msg_id = uuid.uuid4()

        resp_raw = client.call(
            "john smith",
            "testing",
            msg_id
            )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Success")

    def test_invalid_message_delete(self):
        """
        Tests attempting to delete a message that doesn't exist
        """
        logging.info("Starting the test_invalid_message_delete test.")
        client = self.delete_message_client

        msg_id = uuid.uuid4()

        resp_raw = client.call(
            "john smith",
            "testing",
            msg_id
            )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["message"], "Unable to delete message")

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
