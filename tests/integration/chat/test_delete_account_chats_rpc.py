"""
Integration tests for the delete account chats RPC.
"""

import os
# import uuid
import json
import logging

from lib import AutocleanTestCase
from shared.rpcs.delete_account_chats_rpc import DeleteAccountChatsRPCClient
from shared.rpcs.test_rpc import TestRPCClient


class DeleteChatsRPCTest(AutocleanTestCase):
    """
    Integration tests for the delete account chats RPC.
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

        self.delete_account_chats_client = DeleteAccountChatsRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"]
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "delete-account-chats-rpc",
        )


    # def test_delete_chats(self):
    #     """
    #     Tests sending a valid json to delete chats
    #     """
    #     logging.info("Starting the test_delete_chats test.")
    #     client = self.delete_account_chats_client

    #     user_id = str(uuid.uuid4())

    #     resp_raw = client.call(
    #         "john smith",
    #         "testing",
    #         user_id
    #         )

    #     response = json.loads(resp_raw)
    #     logging.info("Response: %s", response)

    #     self.assertEqual(response["status"], 200)
    #     self.assertEqual(response["data"]["message"], "Success")

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
