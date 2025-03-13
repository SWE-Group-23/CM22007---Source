"""
Integration tests for the register RPC.
"""

import os
import json

from lib import AutocleanTestCase
from shared import rpcs
from shared.rpcs.register_rpc import RegisterRPCClient
from shared.rpcs.test_rpc import TestRPCClient
from shared.models import accounts as models

"""
class Accounts(Model):
    username = columns.Text(primary_key=True)
    password_hash = columns.Text()
    password_salt = columns.Text()
    prev_password_hash = columns.Text()
    prev_password_salt = columns.Text()
    otp_secret = columns.Text()
    backup_code_hash = columns.Text()
    backup_code_salt = columns.Text()
    created_at = columns.DateTime()
    last_login = columns.DateTime()
    suspension_history = columns.List(Suspension)
"""

class RegisterRPCTest(AutocleanTestCase):
    """
    Integration tests for the register service
    in the accounts subsystem.
    """

    def test_non_unique_user(self):
        """
        Tests if the unique user step works
        correctly on good input.
        """

        models.Accounts.create(
            username="Exists",
        )

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc"
        )

        resp_raw = client.call(
            "testing",
            "unique-user",
            {"username": "Exists"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["data"]["unique"], False)

    def test_unique_user(self):
        """
        Tests if the unique user step works
        correctly on bad input.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc"
        )

        resp_raw = client.call(
            "testing",
            "unique-user",
            {"username": "NotExists"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["data"]["unique"], True)
