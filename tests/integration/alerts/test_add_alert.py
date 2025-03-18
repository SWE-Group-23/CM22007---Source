"""
Integration tests for the add-alert RPC.
"""

import os

from lib import AutocleanTestCase
from shared.rpcs.ping_rpc import PingRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class AddAlertRPCTest(AutocleanTestCase):
    """
    Integration tests for the ping RPC.
    """

    def setUp(self):
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.add_alert_client = AddAlertRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "add-alert-rpc",
        )


    def test_add_alert(self):
        """
        Tests adding an alert if the JSON is valid
        """
        client = self.add_alert_client
	#sid = 
	#fr
        response = client.call()

        #self.assertEqual(response, b"Pong!")

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
