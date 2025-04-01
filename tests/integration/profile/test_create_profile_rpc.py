"""
Integration tests for the create account RPC.
"""

import os
import json
import logging

from lib import AutocleanTestCase
from shared.rpcs.create_profile_rpc import CreateProfileRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class CreateProfileRPCTest(AutocleanTestCase):
    """
    Integration tests for the create account RPC.
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

        self.create_profile_client = CreateProfileRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-profile-rpc",
        )


    def test_create_profile(self):
        """
        Tests creating a valid profile.
        """
        logging.info("Starting the test_create_profile test.")
        client = self.create_profile_client

        resp_raw = client.call(
            "asmith",
            "testing",
            "a.smith",
            "adam smith",
            "love sourdough <3",
            "vegan"
            )

        response = json.loads(resp_raw)

        self.assertEqual(response["data"]["status"], "success")
        self.assertEqual(response["status"], 200)

    def test_send_nothing(self):
        """
        Tests sending a poorly formed  account creation
        """
        client = self.test_client

        resp_raw = client.call("")
        response = json.loads(resp_raw)

        logging.info("Response: %s", response)
        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["reason"], "Bad JSON.")
