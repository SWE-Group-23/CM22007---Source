"""
Integration tests for the View Food RPC.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta

import shared
from shared import rpcs
from shared.models import food as model
from shared.rpcs.create_food_rpc import CreateFoodRPCClient
from shared.rpcs.view_food_rpc import ViewFoodRPCClient
from shared.rpcs.test_rpc import TestRPCClient

from lib import AutocleanTestCase

from cassandra.cqlengine.query import DoesNotExist


class ViewFoodRPCTest(AutocleanTestCase):
    """
    Integration tests for View Food RPC.
    """

    def setUp(self):  # pylint: disable=invalid-name
        """
        Sets up the RPC client and Scylla.
        """
        super().setUp()

        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.client = ViewFoodRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "view-food-item-rpc",
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "view-food-item-rpc",
        )
       
    def create_food(self, user, useby):
        """
        Populates the food table for a test user.
        """
        create_food_rpc = CreateFoodRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
        )

        resp_raw = create_food_rpc.call(
            user,
            "testing",
            "Test Food",
            useby,
        )

        response = json.load(resp_raw)
        logging.info("Response: %s", response)

    def test_normal(self):
        """
        Tests viewing standard food items.
        """
        user = "TestUser"

        for _ in range(3):
            useby = (datetime.now() + timedelta(30)).replace(
                second=0,
                microsecond=0,
            )

            self.create_food(user, useby)

        resp_raw = self.client.call(
            auth_user=user,
            srv_from="testing"
        )

        response = json.loads(resp_raw)

        self.assertEqual(response["status"], 200)
        
        food = model.Food.get(user=user)
        # TODO: check the food response is the same as food in table

    def test_empty(self):
        """
        Tests viewing an empty inventory.
        """
        user = "TestUser"

        resp_raw = self.client.call(
            auth_user=user,
            srv_from="testing"
        )

        response = json.load(resp_raw)
        with self.assertRaises(DoesNotExist):
            self.assertEqual(response["status"], 200)

    def test_non_json(self):
        """
        Tests the case where a request is not JSON.
        """
        resp_raw = self.test_client.call("asdfjkl;")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertIsNone(resp["data"].get("message"))
        self.assertEqual(resp["data"]["reason"], "Bad JSON.")

    def test_malformed(self):
        """
        Tests the case where the request is malformed
        JSON.
        """
        req = {"hello": "world"}

        resp_raw = self.test_client.call(json.dumps(req))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertIsNone(resp["data"].get("message"))
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_bad_version(self):
        """
        Tests the case where the request version
        is incorrect.
        """
        req = rpcs.request(
            "",
            "1.2.3",
            "testing",
            label="testing food",
        )

        resp_raw = self.test_client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertIsNone(resp["data"].get("message"))
        self.assertEqual(resp["data"]["reason"], "Bad version.")
