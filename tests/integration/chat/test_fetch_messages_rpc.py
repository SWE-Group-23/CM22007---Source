"""
Integration tests for the fetch messages RPC.
"""

import os
import uuid
import time
import json
import logging

from lib import AutocleanTestCase
from shared.rpcs.fetch_messages_rpc import FetchMessagesRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class FetchMessagesRPCTest(AutocleanTestCase):
    """
    Integration tests for the fetch messages RPC.
    """

    def setUp(self):
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        self.fetch_messages_client = FetchMessagesRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "fetch-messages-rpc",
        )


    def test_send_message(self):
        """
        Tests sending a valid fetch request
        """
        logging.info("Starting the test_fetch_messages test.")
        client = self.fetch_messages_client

        chat_id = uuid.uuid4()

        resp_raw = client.call(
            "john smith", 
            "testing", 
            chat_id
            )
        
        response = json.loads(resp_raw)
        logging.info(f"Response {response}")
        logging.info(f"Data received: {response["data"]}")

        self.assertEqual(response["status"], 200)
        #self.assertEqual(response["data"]["message"], "Message sent")

    def test_send_nothing(self):
        """
        Tests sending a poorly formed message request
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "fetch-messages-rpc",
        )

        resp_raw = client.call("")
        response = json.loads(resp_raw)

        logging.info(f"Response: {response}")
        self.assertEqual(response["status"], 400)
        self.assertEqual(response["data"]["reason"], "Bad JSON.")
