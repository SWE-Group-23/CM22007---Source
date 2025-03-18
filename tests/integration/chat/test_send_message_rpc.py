"""
Integration tests for the send message RPC.
"""

import os
import uuid
import time
import json
import logging
from lib import AutocleanTestCase
import shared
from shared.rpcs.send_message_rpc import SendMessageRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class SendMessageRPCTest(AutocleanTestCase):
    """
    Integration tests for the send message RPC.
    """

    def setUp(self):
        """
        Does a set up
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
        Docs
        """
        logging.info("Starting the test_send_message test.")
        print("Starting the test_send_message test.")
        client = self.send_message_client

        chat_id = uuid.uuid4()
        sender_id = uuid.uuid4()
        timestamp = int(time.time() * 1000)
        message = "test message"

        resp_raw = client.call(
            "john smith", 
            "testing", 
            chat_id,
            sender_id,
            timestamp,
            message
            )
        
        response = json.loads(resp_raw)
        print(f"Response {response}")

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Message sent")

    def test_send_nothing(self):
        """
        Docs
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "send-message-rpc",
        )

        response = client.call("")

        response_json = json.loads(response)
        logging.info(f"Response: {response}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json, {"reason": "Malformed request."})
