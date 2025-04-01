"""
Integration tests for the Create Food RPC.
"""

import os
import json
import logging

import uuid
from datetime import datetime, timedelta

from lib import AutocleanTestCase
from shared import rpcs
from shared.rpcs.create_food_rpc import CreateFoodRPCClient
from shared.rpcs.test_rpc import TestRPCClient

class CreateFoodRPCTest(AutocleanTestCase):
    """
    Integration tests for Create Food RPC.
    """

    def test_normal(self):
        """
        Tests creating standard food item.
        """
        logging.info("Starting test: test_normal.")
        client = CreateFoodRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-food-item-rpc"
        )

        food_id = "None"
        img_id = uuid.uuid4()
        label = "Test Food"
        useby = datetime.now() + timedelta(1.0)

        resp_raw = client.call(
            "Test User",
            "testing",
            food_id,
            img_id,
            label,
            useby
        )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Successfully created food item")

    def test_past_useby(self):
        """
        Tests creating food item which has already expired.
        """
        logging.info("Starting test: test_send_nothing.")
        client = CreateFoodRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-food-item-rpc"
        )

        food_id = "None"
        img_id = uuid.uuid4()
        label = ""
        useby = datetime(2025, 1, 1, 0, 0)

        resp_raw = client.call(
            "Test User",
            "testing",
            food_id,
            img_id,
            label,
            useby
        )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["reason"], "Unable to create food item - Already expired")


    def test_non_json(self):
        """
        Tests the case where a request is not JSON.
        """
        test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-food-item-rpc",
        )

        resp_raw = test_client.call("asdfjkl;")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad JSON.")

    def test_malformed(self):
        """
        Tests the case where the request is malformed
        JSON.
        """
        test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-food-item-rpc",
        )

        req = {
            "hello": "world"
        }

        resp_raw = test_client.call(json.dumps(req))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_bad_version(self):
        """
        Tests the case where the request version
        is incorrect.
        """
        test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "create-food-item-rpc",
        )

        req = rpcs.request(
            "",
            "1.2.3",
            "testing",
            {"message": "Ping!"},
        )

        resp_raw = test_client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")
