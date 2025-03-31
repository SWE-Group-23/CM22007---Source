"""
Integration tests for the Create Food RPC.
"""

import os
import json
import logging

import uuid
from datetime import datetime

from lib import AutocleanTestCase
from shared import rpcs
from shared.rpcs.create_food_rpc import CreateFoodRPCClient
from shared.rpcs.test_rpc import TestRPCClient

class CreateFoodRPCTest(AutocleanTestCase):
    """
    Integration tests for Create Food RPC.
    """
    def __init__(self):
        """
        Sets up ScyllaDB and RPC Clients.
        """
        super().__init__()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        self.create_food_client = CreateFoodRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )
       
    def test_normal(self):
        """
        Tests creating standard food item.
        """
        logging.info("Starting test: test_normal.")
        client = self.create_food_client

        food_id = "None"
        user_id = uuid.uuid4()
        img_id = uuid.uuid4()
        label = "Test Food"
        useby = datetime(2025, 1, 1, 0, 0)

        resp_raw = client.call(
            "Test User",
            "testing",
            food_id,
            user_id,
            img_id,
            label,
            useby
        )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 200)
        self.assertEqual(response["data"]["message"], "Successfully created food item")
    
    def test_send_nothing(self):
        """
        Tests creating food item with no given information.
        """
        logging.info("Starting test: test_send_nothing.")
        client = self.create_food_client

        food_id = "None"
        user_id = uuid.uuid4()
        img_id = uuid.uuid4()
        label = ""
        useby = ""

        resp_raw = client.call(
            "Test User",
            "testing",
            food_id,
            user_id,
            img_id,
            label,
            useby
        )
        
        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["message"], "Unable to create food item")


    def test_incorrect_format(self):
        """
        Tests creating food item in incorrect format.
        """
        logging.info("Starting test: test_send_nothing.")
        client = self.create_food_client

        food_id = "None"
        user_id = uuid.uuid4()
        img_id = uuid.uuid4()
        label = ""
        useby = datetime(2025, 17, 17, 0, 0)

        resp_raw = client.call(
            "Test User",
            "testing",
            food_id,
            user_id,
            img_id,
            label,
            useby
        )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["message"], "Unable to create food item")
    
    def test_past_useby(self):
        """
        Tests creating food item which has already expired.
        """
        logging.info("Starting test: test_send_nothing.")
        client = self.create_food_client

        food_id = "None"
        user_id = uuid.uuid4()
        img_id = uuid.uuid4()
        label = ""
        useby = datetime(2025, 1, 1, 0, 0)

        resp_raw = client.call(
            "Test User",
            "testing",
            food_id,
            user_id,
            img_id,
            label,
            useby
        )

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["message"], "Unable to create food item")


    def test_non_json(self):
        """
        Tests the case where a request is not JSON.
        """

        resp_raw = self.test_client.call("asdfjkl;")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad JSON.")

    def test_malformed(self):
        """
        Tests the case where the request is malformed
        JSON.
        """

        req = {
            "hello": "world"
        }

        resp_raw = self.test_client.call(json.dumps(req))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
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
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")

