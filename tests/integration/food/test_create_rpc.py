"""
Integration tests for the Create Food RPC.
"""

import os
import json

from lib import AutocleanTestCase
# from shared.rpcs.food_rpc import FoodRPCClient?
from shared import rpcs
from shared.rpcs.test_rpc import TestRPCClient

class CreateFoodRPCTest(AutocleanTestCase):
    """
    Integration tests for Create Food RPC.
    """

    # test creating valid food item
    # test creating invalid food item - incorrect date format, etc
    # test creating food item that already exists
    # test creating food item that expires same day 
    # test alerts send when needed
    
    def test_non_json(self):
        """
        Tests the case where a request is not JSON.
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        resp_raw = client.call("asdfjkl;")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad JSON.")

    def test_malformed(self):
        """
        Tests the case where the request is malformed
        JSON.
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        req = {
            "hello": "world"
        }

        resp_raw = client.call(json.dumps(req))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_bad_version(self):
        """
        Tests the case where the request version
        is incorrect.
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        req = rpcs.request(
            "",
            "1.2.3",
            "testing",
            {"message": "Ping!"},
        )

        resp_raw = client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")

