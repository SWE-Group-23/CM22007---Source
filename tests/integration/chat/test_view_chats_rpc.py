"""
Integration tests for the view chats RPC.
"""

import os
import json
import logging

from lib import AutocleanTestCase
from shared import rpcs
from shared.rpcs.view_chats_rpc import ViewChatsRPCClient
from shared.rpcs.create_chat_rpc import CreateChatRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class ViewChatsRPCTest(AutocleanTestCase):
    """
    Integration tests for the view chats RPC.
    """

    def setUp(self):  # pylint: disable=invalid-name
        """
        Sets up Scylla and RPC Clients.
        """
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.view_chats_client = ViewChatsRPCClient(
            os.environ["RABBITMQ_USERNAME"], os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "view-chats-rpc",
        )

    def _add_chats(self, user1, user2):
        create_chat_rpc = CreateChatRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )
        resp_raw = create_chat_rpc.call(
            user1,
            "testing",
            user2,
        )
        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

    def test_view_chats(self):
        """
        Tests sending a valid fetch request
        """
        logging.info("Starting the test_view_chats test.")
        client = self.view_chats_client

        # Populate the db with actual chats
        self._add_chats("john smith", "bob")
        self._add_chats("alice", "john smith")
        self._add_chats("alice", "bob")

        resp_raw = client.call("john smith", "testing")

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)
        logging.info("Data received: %s", response["data"])

        self.assertEqual(response["status"], 200)

    def test_view_no_chats(self):
        """
        Tests sending a valid fetch request but there are no chats
        """
        logging.info("Starting the test_view_no_chats test.")
        client = self.view_chats_client

        resp_raw = client.call("john smith", "testing")

        response = json.loads(resp_raw)
        logging.info("Response: %s", response)
        logging.info("Data received: %s", response["data"])

        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["message"], "No chats to find")

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

    def test_bad_version(self):
        """
        Tests the case where the request version
        is incorrect.
        """
        client = self.test_client

        req = rpcs.request(
            "",
            "1.2.3",
            "testing",
            {"message": "Bad test"},
        )

        resp_raw = client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")

    def test_malformed(self):
        """
        Tests the case where the request is malformed
        JSON.
        """
        client = self.test_client

        req = {"hello": "world"}

        resp_raw = client.call(json.dumps(req))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")
