"""
Integration tests for the suspend account RPC
in the accounts subsystem.
"""

import os
import json
import uuid
import logging
from datetime import datetime as dt
from datetime import timedelta

import pyotp
import argon2

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
            "login-rpc",
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

        self.suspend_client.call(
            auth_mod="DummyModerator",
            srv_from="testing",
            username="Exists",
            suspend_until=str(dt.now() + timedelta(weeks=2)),
        )

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
        self.assertGreaterEqual(dt.now() + timedelta(weeks=2), sus.end)
