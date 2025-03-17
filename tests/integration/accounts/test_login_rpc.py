"""
Integration tests for the login RPC.
"""

import os
import json
import uuid
import logging
import datetime

import valkey
import argon2
import pyotp

from lib import AutocleanTestCase
import shared
from shared.rpcs.login_rpc import LoginRPCClient
from shared.rpcs.test_rpc import TestRPCClient
from shared.models import accounts as model


class LoginRPCTest(AutocleanTestCase):
    """
    Integration tests for the login service
    in the accounts subsystem.
    """

    def setUp(self):  # pylint: disable=invalid-name
        """
        Sets up Valkey, Scylla, RPC Clients, and Argon2.
        """
        super().setUp()

        # suppress new default session warning
        logging.getLogger("cassandra.cqlengine.connection").setLevel(logging.ERROR)

        # setup valkey
        self.vk = valkey.Valkey(
            host="accounts-valkey.accounts.svc.cluster.local",
            port="6379",
            db=0,
            username=os.environ["ACCOUNTS_VALKEY_USERNAME"],
            password=os.environ["ACCOUNTS_VALKEY_PASSWORD"],
        )

        # setup scylla
        _ = shared.setup_scylla(
            "kc5hm6rrldpq76bbbclsn6s31cdig",
            user=os.environ["SCYLLADB_USERNAME"],
            password=os.environ["SCYLLADB_PASSWORD"],
        )

        self.login_client = LoginRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "login-rpc",
        )

        # setup argon
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
            model.Accounts.if_not_exists().create(
                username=username,
                password_hash=self.ph.hash(pw_digest),
                otp_secret=pyotp.random_base32(),
                backup_code_hash=self.ph.hash(backup_code),
                created_at=datetime.datetime.now(),
            )
        )

        return pw_digest

    def test_username_password(self):
        """
        Tests checking good/bad username/password
        combinations.
        """

        # create dummy user
        self._create_user()

        # combinations to test
        usernames = ["Exists", "NotExists"]
        passwords = ["dummy-password", "not-the-password"]
        combinations = [
            (
                str(uuid.uuid4()),
                user,
                pw,
                user == "Exists" and pw == "dummy-password",
            )
            for user in usernames
            for pw in passwords
        ]

        for token, user, pw, correct in combinations:
            # subtest each combination
            with self.subTest(token=token, user=user, pw=pw, correct=correct):
                resp = self.login_client.user_pw_call(
                    token,
                    "testing",
                    user,
                    self.ph.hash(pw, salt=user.ljust(16, "=").encode()),
                )

                self.assertEqual(resp["status"], 200)
                self.assertEqual(resp["data"]["correct"], correct)

                # check Valkey
                vk_data_raw = self.vk.get(f"login:{token}")
                if correct:
                    self.assertIsNotNone(vk_data_raw)
                    vk_data = json.loads(vk_data_raw)
                    self.assertEqual(vk_data["stage"], "username-password")
                    self.assertEqual(vk_data["username"], user)
                else:
                    self.assertIsNone(vk_data_raw)

    def test_malformed_username_password(self):
        """
        Tests a variety of different malformed
        username and password combinations.
        """

        # dummy user
        pw_digest = self._create_user()

        # combinations to test
        usernames = [
            "Exists",
            True,
            1,
            1.0,
            ["Exists"],
            {"username": "Exists"},
        ]
        passwords = [
            pw_digest,
            True,
            1,
            1.0,
            [pw_digest],
            {"password_digest": pw_digest},
        ]

        for i, user in enumerate(usernames):
            for j, pw in enumerate(passwords):
                correct = False
                if i == j == 0:
                    correct = True

                token = str(uuid.uuid4())

                with self.subTest(
                    token=token,
                    user=user,
                    pw=pw,
                    correct=correct,
                ):
                    resp = self.login_client.user_pw_call(
                        token,
                        "testing",
                        user,
                        pw,
                    )

                    if correct:
                        self.assertEqual(resp["status"], 200)
                        self.assertTrue(resp["data"]["correct"])
                    else:
                        self.assertEqual(resp["status"], 400)
                        self.assertEqual(
                            resp["data"]["reason"],
                            "Malformed request.",
                        )

                    # check Valkey
                    vk_data_raw = self.vk.get(f"login:{token}")
                    if correct:
                        self.assertIsNotNone(vk_data_raw)
                        vk_data = json.loads(vk_data_raw)
                        self.assertEqual(vk_data["stage"], "username-password")
                        self.assertEqual(vk_data["username"], user)
                    else:
                        self.assertIsNone(vk_data_raw)

    def test_username_password_wrong_stage(self):
        """
        Tests the username-password call where
        the token has the wrong Valkey stage.
        """
        pw_digest = self._create_user()
        token = str(uuid.uuid4())
        stage = json.dumps({"step": "username-password", "username": "Exists"})

        self.vk.set(f"login:{token}", stage)

        resp = self.login_client.user_pw_call(
            token,
            "testing",
            "Exists",
            pw_digest,
        )

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")

        vk_raw = self.vk.get(f"login:{token}")
        self.assertEqual(stage, vk_raw.decode())
