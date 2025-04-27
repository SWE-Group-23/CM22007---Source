"""
Integration tests for the Create Food RPC.
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
from shared.rpcs.test_rpc import TestRPCClient

from lib import AutocleanTestCase

from cassandra.cqlengine.query import DoesNotExist


class CreateFoodRPCTest(AutocleanTestCase):
    """
    Integration tests for Create Food RPC.
    """

    def setUp(self):  # pylint: disable=invalid-name
        """
        Sets up the RPC client and Scylla.
        """
        super().setUp()

        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.client = CreateFoodRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-food-item-rpc",
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-food-item-rpc",
        )

        _ = shared.setup_scylla(
            "kcpnmup1dddinisrgc5hma",
            user=os.environ["SCYLLADB_USERNAME"],
            password=os.environ["SCYLLADB_PASSWORD"],
        )

    def test_normal(self):
        """
        Tests creating standard food item.
        """
        user = "TestUser"
        img_id = uuid.uuid4()
        label = "Test Food"
        description = "Test Food Description"
        useby = (datetime.now() + timedelta(30)).replace(
            second=0,
            microsecond=0,
        )

        resp_raw = self.client.call(
            auth_user=user,
            srv_from="testing",
            img_id=img_id,
            label=label,
            useby=useby,
            description=description,
        )

        response = json.loads(resp_raw)

        self.assertEqual(response["status"], 200)
        self.assertEqual(
            response["data"]["message"],
            "Successfully created food item",
        )

        food = model.Food.get(user=user)
        self.assertIsNotNone(food)
        self.assertEqual(food["user"], user)
        self.assertEqual(food["img_id"], img_id)
        self.assertEqual(food["label"], label)
        self.assertEqual(food["description"], description)
        self.assertEqual(food["useby"], useby)

    def test_past_useby(self):
        """
        Tests creating food item which has already expired.
        """
        img_id = uuid.uuid4()
        user = "TestUser"
        label = ""
        useby = datetime(2025, 1, 1, 0, 0)

        resp_raw = self.client.call(
            auth_user=user,
            srv_from="testing",
            img_id=img_id,
            label=label,
            useby=useby,
        )

        response = json.loads(resp_raw)

        self.assertEqual(response["status"], 400)
        self.assertEqual(
            response["data"]["reason"],
            "Expiry datetime cannot be before now.",
        )

        with self.assertRaises(DoesNotExist):
            model.Food.get(user=user)

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
            {"message": "Ping!"},
        )

        resp_raw = self.test_client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertIsNone(resp["data"].get("message"))
        self.assertEqual(resp["data"]["reason"], "Bad version.")
