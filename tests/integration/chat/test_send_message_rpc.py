"""
Integration tests for the send message RPC.
"""

import os
import uuid
import json
import logging
from datetime import datetime

from lib import AutocleanTestCase
from shared import rpcs
from shared.rpcs.send_message_rpc import SendMessageRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class SendMessageRPCTest(AutocleanTestCase):
    """
    Integration tests for the send message RPC.
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

        self.send_message_client = SendMessageRPCClient(
            os.environ["RABBITMQ_USERNAME"], os.environ["RABBITMQ_PASSWORD"]
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
        receiver_user = str("Bob")
        timestamp = str(datetime.now())
        message = "test message"

        resp_raw = client.call(
            "john smith",
            "testing",
            chat_id,
            receiver_user,
            timestamp,
            message,
        )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        print(response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Message sent")

    def test_send_new_chat_message(self):
        """
        Tests sending a message to a new chat
        """
        logging.info("Starting the test_send_new_chat_message test.")
        client = self.send_message_client

        chat_id = "None"
        receiver_user = str("Alice")
        timestamp = str(datetime.now())
        message = "New chat test message"

        resp_raw = client.call(
            "john smith",
            "testing",
            chat_id,
            receiver_user,
            timestamp,
            message,
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

    def test_bad_version(self):
        """
        Tests the case where the request version
        is incorrect.
        """
        client = self.test_client

        req = rpcs.request(
            "",
            "1.2.3",
            "testing",
            {"message": "Bad test"},
        )

        resp_raw = client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")

    def test_malformed(self):
        """
        Tests the case where the request is malformed
        JSON.
        """
        client = self.test_client

        req = {"hello": "world"}

        resp_raw = client.call(json.dumps(req))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")
