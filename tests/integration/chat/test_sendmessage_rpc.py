"""
Integration tests for the send message RPC.
"""

import os
import uuid
import time
import json
from lib import AutocleanTestCase
from shared.rpcs.sendmessage_rpc import SendMessageRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class SendMessageRPCTest(AutocleanTestCase):
    """
    Integration tests for the send message RPC.
    """

    def test_send_message(self):
        """
        Docs
        """
        client = SendMessageRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "sendmessage-rpc",
        )

        response = client.call(
            "john smith", 
            "send-message", 
            uuid.uuid4(),
            uuid.uuid4(),
            int(time.time() * 1000),
            "test message"
            )
        response_json = json.loads(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json, {"message": "Message sent"})

    def test_send_nothing(self):
        """
        Docs
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "sendmessage-rpc",
        )

        response = client.call("")

        response_json = json.loads(response)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json, {"reason": "Malformed request."})
