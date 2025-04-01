"""
Integration tests for the ping RPC.
"""

import os
import json

from lib import AutocleanTestCase
from shared import rpcs
from shared.rpcs.ping_rpc import PingRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class PingRPCTest(AutocleanTestCase):
    """
    Integration tests for the ping RPC.
    """

    def test_send_ping(self):
        """
        Test expected "Ping!" for a
        "Pong!" response.
        """
        client = PingRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        resp_raw = client.call("testing")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertRaises(KeyError, lambda x: x["data"]["reason"], resp)
        self.assertEqual(resp["data"]["message"], "Pong!")

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

        req = rpcs.request(
            "",
            "1.0.0",
            "testing",
            {"message": ""},
        )

        resp_raw = client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["reason"], resp)
        self.assertEqual(resp["data"]["message"], "That's not a ping!")

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
            "200",
            "testing",
            {"message": "Ping!"},
        )

        resp_raw = client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")
