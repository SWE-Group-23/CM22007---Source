"""
Integration tests for the view profile RPC.
"""

import os
import uuid
import json
import logging

from lib import AutocleanTestCase
from shared.rpcs.view_profile_rpc import ViewProfileRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class ViewProfileRPCTest(AutocleanTestCase):
    """
    Integration tests for the view profile RPC.
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

        self.view_profile_client = ViewProfileRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "view-profile-rpc",
        )


    def test_view_profile(self):
        """
        Tests sending a valid fetch request
        """
        logging.info("Starting the test_view_chats test.")
        client = self.view_profile_client

        resp_raw = client.call(
            "j.smith",
            "testing",
            "a.smith"
            )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)
        logging.info("Data received: %s", response["data"])

        self.assertEqual(response["status"], 200)

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