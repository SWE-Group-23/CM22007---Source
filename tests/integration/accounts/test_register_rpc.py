"""
Integration tests for the register RPC.
"""

import os
import json
import uuid
import time
import logging
from types import SimpleNamespace

import valkey
import argon2
import pyotp

from lib import AutocleanTestCase
import shared
from shared import rpcs
from shared.rpcs.register_rpc import RegisterRPCClient
from shared.rpcs.test_rpc import TestRPCClient
from shared.models import accounts as models


class RegisterRPCTest(AutocleanTestCase):  # pylint: disable=too-many-public-methods
    """
    Integration tests for the register service
    in the accounts subsystem.
    """

    def setUp(self):  # pylint: disable=invalid-name
        """
        Sets up Valkey, Scylla, RPC Clients, and Argon2.
        """
        super().setUp()

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection").setLevel(logging.ERROR)

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

        self.reg_client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
        )

        self.test_client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # setup argon
        self.ph = argon2.PasswordHasher()

    def _advance_to_stage(
        self,
        target_stage: str,
        username="NotExists",
        password="dummy-password",
    ) -> SimpleNamespace:
        """
        Advances to a stage in the registration, returning
        the context at that point.

        Args:
            target_stage: str - the name of the Valkey stage to advance to.
            username="NotExists" - the username to use.
            password="dummy-password" - the password to use.

        Returns:
            SimpleNamespace - the context, has:
                sid - the session ID used.
                username - same as given in args.
                password - same as given in args.
                otp_uri - the OTP uri if past "setting-up-otp"
                otp_secret - the OTP secret if past "setting-up-otp"
                backup_code - the backup code if at "backup-code-generated"
                vk_data - current Valkey stage.
        """
        # ad-hoc obj to store context
        context = SimpleNamespace(
            sid=str(uuid.uuid4()),
            username=username,
            password=password,
            otp_uri=None,
            otp_secret=None,
            backup_code=None,
            vk_data=None,
        )

        # define stages
        stages = {
            "username-valid": {
                "execute": lambda: (
                    self.reg_client.check_valid_username_call(
                        context.sid, "testing", context.username
                    )
                ),
                "post": None,
            },

            "password-set": {
                "execute": lambda: self.reg_client.set_password_call(
                    context.sid, "testing", context.password
                ),
                "post": None,
            },

            "setting-up-otp": {
                "execute": lambda: self.reg_client.setup_otp_call(
                    context.sid, "testing"
                ),
                "post": lambda resp: (
                    setattr(context, "otp_uri", resp["data"]["prov_uri"]),
                    setattr(
                        context, "otp_secret", pyotp.parse_uri(
                            context.otp_uri).secret
                    ),
                ),
            },

            "otp-verified": {
                "execute": lambda: self.reg_client.verify_otp_call(
                    context.sid, "testing", pyotp.TOTP(
                        context.otp_secret).now()
                ),
                "post": None,
            },

            "backup-code-generated": {
                "execute": lambda: self.reg_client.backup_code_call(
                    context.sid, "testing"
                ),
                "post": lambda resp: setattr(
                    context, "backup_code", resp["data"]["backup_code"]
                ),
            },
        }

        # define stage order
        stage_order = [
            "username-valid",
            "password-set",
            "setting-up-otp",
            "otp-verified",
            "backup-code-generated",
        ]

        # check target stage exists and get it's index
        try:
            target_index = stage_order.index(target_stage)
        except ValueError as exc:
            raise ValueError(f"Invalid target stage: {target_stage}") from exc

        # iterate through until target stage index
        for stage in stage_order[: target_index + 1]:
            # execute the stage
            response = stages[stage]["execute"]()

            # collect data
            if stages[stage]["post"]:
                stages[stage]["post"](response)

            # update Valkey data snapshot
            context.vk_data = self._get_vk_data(context.sid)

        return context

    def _get_vk_data(self, sid: str) -> dict | None:
        """
        Get the valkey data as a dict if
        possible.
        """
        vk_raw = self.vk.get(f"register:{sid}")
        return json.loads(vk_raw) if vk_raw else None

    def _assert_vk_stage(
        self,
        sid: str,
        expected_stage: str,
        expected_username: str
    ) -> None:
        """
        Asserts that the Valkey stage is correct.
        """
        stage_raw = self.vk.get(f"register:{sid}")
        self.assertIsNotNone(stage_raw, "Valkey stage not found.")
        stage = json.loads(stage_raw)
        self.assertEqual(stage["stage"], expected_stage)
        self.assertEqual(stage["username"], expected_username)

    def test_backup_code(self):
        """
        Tests getting a backup code.
        """
        ctx = self._advance_to_stage("otp-verified")
        resp = self.reg_client.backup_code_call(ctx.sid, "testing")

        # update valkey data
        ctx.vk_data = self._get_vk_data(ctx.sid)

        self.assertEqual(resp["status"], 200)
        self.assertRegex(
            resp["data"]["backup_code"],
            "^[0-9a-f]{6}-[0-9a-f]{6}-[0-9a-f]{6}-[0-9a-f]{6}$",
        )

        # would throw query.DoesNotExist if user didn't exist
        user = models.Accounts.get(username="NotExists")

        # check database
        self.assertEqual(user["otp_secret"], ctx.otp_secret)
        self.assertTrue(self.ph.verify(
            user["password_hash"], "dummy-password"))
        self.assertTrue(
            self.ph.verify(user["backup_code_hash"],
                           resp["data"]["backup_code"])
        )
        self.assertIsNotNone(user["created_at"])
        self.assertIsNone(user["last_login"])
        self.assertIsNone(user["prev_password_hash"])

        # check valkey
        self.assertIsNone(ctx.vk_data)

    def test_backup_code_wrong_stage(self):
        """
        Tests getting a backup code with the wrong
        Valkey stage.
        """
        ctx = self._advance_to_stage("username-valid")

        # try to get a backup code
        resp = self.reg_client.backup_code_call(ctx.sid, "testing")

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")
        self._assert_vk_stage(ctx.sid, "username-valid", ctx.username)

    def test_backup_code_no_stage(self):
        """
        Tests getting a backup code with no
        Valkey stage.
        """
        sid = str(uuid.uuid4())

        # try to get a backup code
        resp = self.reg_client.backup_code_call(sid, "testing")

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

        vk_stage_raw = self.vk.get(f"register:{sid}")
        self.assertIsNone(vk_stage_raw)

    def test_verify_otp(self):
        """
        Tests verifying an OTP.
        """
        ctx = self._advance_to_stage("setting-up-otp")

        # create TOTP with prov uri
        totp = pyotp.parse_uri(ctx.otp_uri)

        # call with current OTP
        resp = self.reg_client.verify_otp_call(
            ctx.sid,
            "testing",
            totp.now(),
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["correct"])

        self._assert_vk_stage(ctx.sid, "otp-verified", ctx.username)
        # check hash still there (would throw KeyError if not)
        _ = ctx.vk_data["hash"]
        self.assertEqual(ctx.vk_data["otp_sec"], totp.secret)

    def test_verify_otp_wrong_otp(self):
        """
        Tests verifying an OTP with the wrong
        OTP.
        """
        ctx = self._advance_to_stage("setting-up-otp")

        # create TOTP with prov uri
        totp = pyotp.parse_uri(ctx.otp_uri)

        otp = "123456"

        # if this ever happens i will buy a lottery ticket
        if totp.verify(otp):
            otp = "654321"

        # call with wrong OTP
        resp = self.reg_client.verify_otp_call(
            ctx.sid,
            "testing",
            otp,
        )

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["correct"])

        self._assert_vk_stage(ctx.sid, "setting-up-otp", ctx.username)

    def test_verify_otp_no_otp(self):
        """
        Tests verifying an OTP when no
        OTP given.
        """
        ctx = self._advance_to_stage("setting-up-otp")

        # call with wrong OTP
        resp_raw = self.reg_client.call(
            ctx.sid,
            "testing",
            "verify-otp",
            {},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

        self._assert_vk_stage(ctx.sid, "setting-up-otp", ctx.username)

    def test_verify_otp_malformed_otp(self):
        """
        Tests verifying an OTP with too long
        of an OTP.
        """

        ctx = self._advance_to_stage("setting-up-otp")

        # call with malformed OTP
        resp = self.reg_client.verify_otp_call(
            ctx.sid,
            "testing",
            "1234567",
        )

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["correct"])

        self._assert_vk_stage(ctx.sid, "setting-up-otp", ctx.username)

    def test_verify_otp_int(self):
        """
        Tests verifying an OTP with an integer
        instead.
        """

        ctx = self._advance_to_stage("setting-up-otp")

        # create TOTP with prov uri
        totp = pyotp.parse_uri(ctx.otp_uri)

        # call with current OTP
        resp = self.reg_client.verify_otp_call(
            ctx.sid,
            "testing",
            int(totp.now()),
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["correct"])

        self._assert_vk_stage(ctx.sid, "otp-verified", ctx.username)
        # check hash still there (would throw KeyError if not)
        _ = ctx.vk_data["hash"]
        self.assertEqual(ctx.vk_data["otp_sec"], totp.secret)

    def test_verify_otp_wrong_stage(self):
        """
        Tests verifying an OTP with the wrong
        Valkey stage.
        """

        ctx = self._advance_to_stage("username-valid")

        # call with an OTP
        resp = self.reg_client.verify_otp_call(
            ctx.sid,
            "testing",
            "123456",
        )

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")

        self._assert_vk_stage(ctx.sid, "username-valid", ctx.username)

    def test_verify_otp_no_stage(self):
        """
        Tests verifying an OTP with no Valkey
        stage.
        """

        sid = str(uuid.uuid4())
        resp = self.reg_client.verify_otp_call(
            sid,
            "testing",
            "123456",
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_setup_otp(self):
        """
        Tests setting up an OTP.
        """
        ctx = self._advance_to_stage("password-set")

        # setup OTP
        resp = self.reg_client.setup_otp_call(
            ctx.sid,
            "testing",
        )

        self.assertEqual(resp["status"], 200)

        # update Valkey data
        ctx.vk_data = self._get_vk_data(ctx.sid)

        # would throw an error if the uri was invalid
        totp = pyotp.parse_uri(resp["data"]["prov_uri"])

        self._assert_vk_stage(ctx.sid, "setting-up-otp", ctx.username)
        # check hash still there (would throw KeyError if not)
        _ = ctx.vk_data["hash"]
        self.assertEqual(ctx.vk_data["otp_sec"], totp.secret)
        self.assertEqual(resp["data"]["secret"], totp.secret)

    def test_setup_otp_wrong_stage(self):
        """
        Tests setting up OTP when at wrong stage.
        """
        ctx = self._advance_to_stage("username-valid")

        resp = self.reg_client.setup_otp_call(
            ctx.sid,
            "testing",
        )

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")
        self._assert_vk_stage(ctx.sid, "username-valid", ctx.username)

    def test_setup_otp_no_stage(self):
        """
        Tests setting up an OTP where the token
        does not have a Valkey stage.
        """
        sid = str(uuid.uuid4())
        resp = self.reg_client.setup_otp_call(
            sid,
            "testing",
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_token_ttl_set_password(self):
        """
        Tests if a token times out correctly.
        """
        sid = str(uuid.uuid4())
        stage = json.dumps(
            {
                "stage": "username-valid",
                "username": "NotExists",
            }
        )
        self.vk.setex(f"register:{sid}", 1, stage)

        vk_stage = self.vk.get(f"register:{sid}")
        self.assertIsNotNone(vk_stage)

        time.sleep(2)

        vk_stage = self.vk.get(f"register:{sid}")
        self.assertIsNone(vk_stage)

        resp = self.reg_client.set_password_call(
            sid, "testing", "this-is-a-dummy-value")

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_set_password(self):
        """
        Tests if the set password helper
        call works.
        """
        ctx = self._advance_to_stage("username-valid")

        resp = self.reg_client.set_password_call(
            ctx.sid, "testing", "dummy-password")

        ctx.vk_data = self._get_vk_data(ctx.sid)

        self.assertEqual(resp["status"], 200)
        self._assert_vk_stage(ctx.sid, "password-set", ctx.username)
        self.assertFalse(self.ph.check_needs_rehash(ctx.vk_data["hash"]))
        self.assertTrue(self.ph.verify(ctx.vk_data["hash"], "dummy-password"))

    def test_set_password_wrong_stage(self):
        """
        Tests that the register service does not
        allow a user to set their password
        until their username has been validated.
        """
        sid = str(uuid.uuid4())
        stage_bad = json.dumps({"stage": "bad-stage", "username": "test"})
        self.vk.setex(f"register:{sid}", 60*30, stage_bad)

        resp = self.reg_client.set_password_call(
            sid, "testing", "dummy-password")

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")

    def test_set_password_no_stage(self):
        """
        Tests that the register service does
        not allow a user to set their password
        if they have no stage set.
        """
        sid = str(uuid.uuid4())
        resp = self.reg_client.set_password_call(
            sid, "testing", "dummy-password")

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_set_password_no_digest(self):
        """
        Tests that the register service handles
        not being passed a digest correctly.
        """
        ctx = self._advance_to_stage("username-valid")

        resp_raw = self.reg_client.call(
            ctx.sid,
            "testing",
            "set-password",
            {"password": "dummy-password"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_set_password_bad_digest(self):
        """
        Tests that the register service handles
        not being passed the correct type of
        password digest.
        """
        ctx = self._advance_to_stage("username-valid")

        resp_raw = self.reg_client.call(
            ctx.sid,
            "testing",
            "set-password",
            {"password-digest": True},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_check_non_unique_user(self):
        """
        Tests if the verify user step works
        correctly on already existant username.
        """
        models.Accounts.create(
            username="Exists",
        )

        sid = str(uuid.uuid4())
        resp = self.reg_client.check_valid_username_call(
            sid,
            "testing",
            "Exists",
        )

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])
        self.assertIsNone(self.vk.get(f"register:{sid}"))

    def test_check_bad_username(self):
        """
        Tests many cases where the username
        is badly formatted.
        """
        test_cases = [
            "_user", "user_", ".user_", "user", "us£rname", "us rname"
        ]

        for username in test_cases:
            with self.subTest(username=username):
                sid = str(uuid.uuid4())
                resp = self.reg_client.check_valid_username_call(
                    sid,
                    "testing",
                    username,
                )
                self.assertEqual(resp["status"], 200)
                self.assertFalse(resp["data"]["valid"])
                self.assertIsNone(self.vk.get(f"register:{sid}"))

    def test_check_valid_user(self):
        """
        Tests if the check valid user step works
        correctly on unique and valid username.
        """

        sid = str(uuid.uuid4())
        resp = self.reg_client.check_valid_username_call(
            sid,
            "testing",
            "NotExists",
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["valid"])
        self._assert_vk_stage(sid, "username-valid", "NotExists")

    def test_check_unique_none(self):
        """
        Tests if the uniue user step
        responds correctly given nothing.
        """

        resp_raw = self.reg_client.call(
            "testing",
            "testing",
            "check-valid-username",
            {},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_register_non_json(self):
        """
        Tests if the register RPC responds
        correctly to a non-json request.
        """

        resp_raw = self.test_client.call("asdfjkl;")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad JSON.")

    def test_register_malformed(self):
        """
        Tests if the register RPC responds
        correctly to malformed requests.
        """

        resp_raw = self.test_client.call(json.dumps({"hello": "world"}))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_register_bad_version(self):
        """
        Tests the case where the version
        is not supported.
        """
        req = rpcs.request_unauth(
            "testing",
            "200",
            "testing",
            {"message": "Ping!"},
        )

        resp_raw = self.test_client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")

    def test_register_bad_step_type(self):
        """
        Tests the case where the step
        is not the correct type.
        """

        resp_raw = self.reg_client.call(
            "testing",
            "testing",
            True,
            {},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Unknown step.")
