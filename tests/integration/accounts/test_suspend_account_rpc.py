"""
Integration tests for the suspend account RPC
in the accounts subsystem.
"""

import os
import json
import logging
from datetime import datetime as dt
from datetime import timedelta

import pyotp
import argon2
from cassandra.cqlengine import query as cq

from lib import AutocleanTestCase
import shared
from shared.rpcs.suspend_account_rpc import SuspendAccountRPCClient
from shared.rpcs.test_rpc import TestRPCClient
from shared.models import accounts as model


class SuspendAccountRPCTest(AutocleanTestCase):
    """
    Integration tests for the suspend account service
    in the accounts subsystem.
    """

    def setUp(self):  # pylint: disable=invalid-name
        """
        Sets up ScyllaDB, RPC Clients, and Argon2
        for dummy account creation.
        """
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection",
        ).setLevel(logging.ERROR)

        # setup scylla
        _ = shared.setup_scylla(
            "kc5hm6rrldpq76bbbclsn6s31cdig",
            user=os.environ["SCYLLADB_USERNAME"],
            password=os.environ["SCYLLADB_PASSWORD"],
        )

        # RPC clients
        self.suspend_client = SuspendAccountRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "suspend-account-rpc",
        )

        self.ph = argon2.PasswordHasher()

    def _create_user(
        self,
        username="Exists",
        password="dummy-password",
        backup_code="dummy-backup-code",
    ):
        """
        Creates a user in the database.
        """
        pw_digest = self.ph.hash(
            password,
            salt=username.ljust(16, "=").encode(),
        )

        (
            model.Accounts.create(
                username=username,
                password_hash=self.ph.hash(pw_digest),
                otp_secret=pyotp.random_base32(),
                backup_code_hash=self.ph.hash(backup_code),
                created_at=dt.now(),
            )
        )

    def test_suspend_user(self):
        """
        Tests successfully suspending a user.
        """

        self._create_user()

        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["success"])

        user = model.Accounts.get(username="Exists")

        self.assertEqual(len(user.suspension_history), 1)
        sus = user.suspension_history[0]
        self.assertEqual(
            sus.suspended_by,
            "DummyModerator",
        )
        self.assertIsInstance(sus.start, dt)
        self.assertIsInstance(sus.end, dt)
        self.assertGreaterEqual(dt.now(), sus.start)
        self.assertLess(sus.start, sus.end)
        self.assertGreaterEqual(dt.now() + timedelta(weeks=2), sus.end)

    def test_suspend_nonexistant_user(self):
        """
        Tests suspending a user that doesn't exist.
        """
        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="NotExists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "User does not exist.")
        try:
            (model.Accounts.get(username="NotExists"),)
        except cq.DoesNotExist:
            pass
        else:
            self.fail(
                "Non-existant user created when they shouldn't have been",
            )

    def test_suspend_start_after_end(self):
        """
        Tests suspending a user with a start time after the end time.
        """
        self._create_user()

        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_from=str(dt.now() + timedelta(weeks=2)),
            suspend_until=str(dt.now()),
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(
            resp["data"]["reason"],
            "Start time must be before end time.",
        )

        user = model.Accounts.get(username="Exists")
        self.assertEqual(len(user.suspension_history), 0)

    def test_suspend_not_json(self):
        """
        Tests the suspend account RPC with non-JSON.
        """
        resp_raw = self.test_client.call("not json")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Bad JSON.")

    def test_suspend_json_nothing(self):
        """
        Tests the suspend account RPC with empty JSON.
        """
        resp_raw = self.test_client.call("{}")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_suspend_bad_version(self):
        """
        Tests the suspend RPC with an unsupported version.
        """
        self._create_user()

        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
            api_version="1.2.3",
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Bad version.")
        user = model.Accounts.get(username="Exists")
        self.assertEqual(len(user.suspension_history), 0)

    def test_suspend_wrong_type(self):
        """
        Tests the suspend RPC with a version of the wrong type.
        """
        self._create_user()

        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
            api_version=10,
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Bad version.")
        user = model.Accounts.get(username="Exists")
        self.assertEqual(len(user.suspension_history), 0)

    def test_suspend_bad_date(self):
        """
        Tests the suspend RPC with a malformatted date.
        """
        self._create_user()

        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_until="2030-12-12",
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")
        user = model.Accounts.get(username="Exists")
        self.assertEqual(len(user.suspension_history), 0)

    def test_suspend_no_mod(self):
        """
        Tests the suspend RPC with no moderator.
        """
        self._create_user()

        resp = self.suspend_client.call(
            auth_mod=None,
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")
        user = model.Accounts.get(username="Exists")
        self.assertEqual(len(user.suspension_history), 0)

        resp = self.suspend_client.call(
            auth_mod="",
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")
        user = model.Accounts.get(username="Exists")
        self.assertEqual(len(user.suspension_history), 0)

    def test_multiple_suspensions(self):
        """
        Tests that multiple extensions can be in place.
        """
        self._create_user()

        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=1)),
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["success"])
        user = model.Accounts.get(username="Exists")

        self.assertEqual(len(user.suspension_history), 1)
        sus = user.suspension_history[0]
        self.assertEqual(
            sus.suspended_by,
            "DummyModerator",
        )
        self.assertIsInstance(sus.start, dt)
        self.assertIsInstance(sus.end, dt)
        self.assertGreaterEqual(dt.now(), sus.start)
        self.assertLess(sus.start, sus.end)
        self.assertGreaterEqual(dt.now() + timedelta(weeks=1), sus.end)

        resp = self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["success"])
        user = model.Accounts.get(username="Exists")

        self.assertEqual(len(user.suspension_history), 2)
        sus = user.suspension_history[1]
        self.assertEqual(
            sus.suspended_by,
            "DummyModerator",
        )
        self.assertIsInstance(sus.start, dt)
        self.assertIsInstance(sus.end, dt)
        self.assertGreaterEqual(dt.now(), sus.start)
        self.assertLess(sus.start, sus.end)
        self.assertGreaterEqual(dt.now() + timedelta(weeks=2), sus.end)
