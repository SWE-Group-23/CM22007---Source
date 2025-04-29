"""
Integration tests for the fetch messages RPC.
"""

import os
import uuid
import json
import logging
from datetime import datetime

from lib import AutocleanTestCase
from shared import rpcs
from shared.rpcs.fetch_messages_rpc import FetchMessagesRPCClient
from shared.rpcs.send_message_rpc import SendMessageRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class FetchMessagesRPCTest(AutocleanTestCase):
    """
    Integration tests for the fetch messages RPC.
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

        self.fetch_messages_client = FetchMessagesRPCClient(
            os.environ["RABBITMQ_USERNAME"], os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "fetch-messages-rpc",
        )

    def _add_messages(self, chat_id, message):
        send_message_rpc = SendMessageRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )
        timestamp = str(datetime.now())
        resp_raw = send_message_rpc.call(
            "john smith",
            "testing",
            chat_id,
            "Bob",
            timestamp,
            message
        )
        response = json.loads(resp_raw)
        logging.info("Response: %s", response)

    def test_fetch_message(self):
        """
        Tests sending a valid fetch request
        """
        logging.info("Starting the test_fetch_messages test.")
        client = self.fetch_messages_client

        # Populate the db with actual messages
        chat_id = uuid.uuid4()
        self._add_messages(chat_id, "Testing1")
        self._add_messages(chat_id, "Testing2")
        self._add_messages(chat_id, "Testing3")

        resp_raw = client.call("john smith", "testing", chat_id)

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
