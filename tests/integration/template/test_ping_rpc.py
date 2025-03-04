"""
Integration tests for the ping RPC.
"""

import os

from unittest import TestCase

from shared.rpcs.ping_rpc import PingRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class PingRPCTest(TestCase):
    """
    Integration tests for the ping RPC.
    """

    def test_send_ping(self):
        """
        Test expected "Ping!" for a
        "Pong!" response.
        """
        client = PingRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        response = client.call()

        self.assertEqual(response, b"Pong!")

    def test_send_nothing(self):
        """
        Tests the case where the ping RPC isn't sent the
        correct request.
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        response = client.call("")

        self.assertNotEqual(response, b"Pong")
        self.assertEqual(response, b"That's not a ping!")
