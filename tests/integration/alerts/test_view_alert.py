"""
Integration tests for the add-alert RPC.
"""

import os
import json
import logging
from lib import AutocleanTestCase
from shared.rpcs.view_alert_rpc import ViewAlertRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class ViewAlertRPCTest(AutocleanTestCase):
    """
    Integration tests for the ping RPC.
    """

    def setUp(self): # pylint: disable=invalid-name
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.view_alert_client = ViewAlertRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "view-alert-rpc",
        )

    def test_view_alert(self):
        """
        Tests viewing an alert if the JSON is valid
        """

        logging.info("Starting the test_add_alert test.")

        client = self.view_alert_client
        authuser = "john doe"
        service = "testing"

        response_raw = client.call(authuser, service)
        response = json.loads(response_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"], "this is a test alert")

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
