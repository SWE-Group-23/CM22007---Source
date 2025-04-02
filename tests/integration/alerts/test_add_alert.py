
"""
Integration tests for the add-alert RPC.
"""

import os
import json
import logging
from lib import AutocleanTestCase
from shared.rpcs.add_alert_rpc import AddAlertRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class AddAlertRPCTest(AutocleanTestCase):
    """
    Integration tests for the ping RPC.
    """

    def setUp(self): # pylint: disable=invalid-name
        """
        Setting up RabbitMQ
        """
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

        logging.info("Starting the test_add_alert test.")

        client = self.add_alert_client
        authuser = "john doe"
        service = "testing"
        message = "this is a test alert"

        response_raw = client.call(authuser, service, message)
        response = json.loads(response_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["reason"], "alert added successfully")

    def test_send_nothing(self):
        """
        Tests the case where the add alert RPC isn't sent the
        correct request.
        """
        client = self.test_client
        response_raw = client.call("")
        response = json.loads(response_raw)

        logging.info("Response: %s", response)
        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["reason"], "Invalid JSON")
