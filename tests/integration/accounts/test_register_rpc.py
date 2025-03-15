"""
Integration tests for the register RPC.
"""

import os
import json
import uuid
import time
import logging

import valkey
import argon2
import pyotp

from lib import AutocleanTestCase
import shared
from shared import rpcs
from shared.rpcs.register_rpc import RegisterRPCClient
from shared.rpcs.test_rpc import TestRPCClient
from shared.models import accounts as models


class RegisterRPCTest(AutocleanTestCase):
    """
    Integration tests for the register service
    in the accounts subsystem.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # suppress new default session warning
        logging.getLogger(
            "cassandra.cqlengine.connection").setLevel(logging.ERROR)

        self.vk = valkey.Valkey(
            host="accounts-valkey.accounts.svc.cluster.local",
            port="6379",
            db=0,
            username=os.environ["ACCOUNTS_VALKEY_USERNAME"],
            password=os.environ["ACCOUNTS_VALKEY_PASSWORD"],
        )
        _ = shared.setup_scylla(
            "kc5hm6rrldpq76bbbclsn6s31cdig",
            user=os.environ["SCYLLADB_USERNAME"],
            password=os.environ["SCYLLADB_PASSWORD"],
        )
        self.ph = argon2.PasswordHasher()

    def test_backup_code(self):
        """
        Tests getting a backup code.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # set password
        _ = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        # setup OTP
        resp = client.setup_otp_call(
            auth_user,
            "testing",
        )

        # create TOTP with prov uri
        totp = pyotp.parse_uri(resp["data"]["prov_uri"])

        # call with current OTP
        _ = client.verify_otp_call(
            auth_user,
            "testing",
            totp.now(),
        )

        resp = client.backup_code_call(auth_user, "testing")

        self.assertEqual(resp["status"], 200)
        self.assertRegex(
            resp["data"]["backup_code"],
            "^[0-9a-f]{16}-[0-9a-f]{16}-[0-9a-f]{16}-[0-9a-f]{16}$",
        )

        # would throw query.DoesNotExist if user didn't exist
        user = models.Accounts.get(username="NotExists")

        # check database
        self.assertEqual(user["otp_secret"], totp.secret)
        self.assertTrue(self.ph.verify(
            user["password_hash"], "this-is-a-dummy-value"))
        self.assertTrue(
            self.ph.verify(user["backup_code_hash"],
                           resp["data"]["backup_code"])
        )
        self.assertIsNotNone(user["created_at"])
        self.assertIsNone(user["last_login"])
        self.assertIsNone(user["prev_password_hash"])

        # check valkey
        self.assertIsNone(self.vk.get(f"register:{auth_user}"))

    def test_backup_code_wrong_stage(self):
        """
        Tests getting a backup code with the wrong
        Valkey stage.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to first stage
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # try to get a backup code
        resp = client.backup_code_call(auth_user, "testing")

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")

        vk_stage_raw = self.vk.get(f"register:{auth_user}")
        vk_stage = json.loads(vk_stage_raw)

        self.assertEqual(vk_stage["stage"], "username-valid")

    def test_backup_code_no_stage(self):
        """
        Tests getting a backup code with no
        Valkey stage.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())

        # try to get a backup code
        resp = client.backup_code_call(auth_user, "testing")

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

        vk_stage_raw = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage_raw)

    def test_verify_otp(self):
        """
        Tests verifying an OTP.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # set password
        _ = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        # setup OTP
        resp = client.setup_otp_call(
            auth_user,
            "testing",
        )

        # create TOTP with prov uri
        totp = pyotp.parse_uri(resp["data"]["prov_uri"])

        # call with current OTP
        resp = client.verify_otp_call(
            auth_user,
            "testing",
            totp.now(),
        )

        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["data"], {})

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "otp-verified")
        self.assertEqual(stage["username"], "NotExists")
        # check hash still there (would throw KeyError if not)
        _ = stage["hash"]
        self.assertEqual(stage["otp_sec"], totp.secret)

    def test_verify_otp_wrong_otp(self):
        """
        Tests verifying an OTP with the wrong
        OTP.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # set password
        _ = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        # setup OTP
        resp = client.setup_otp_call(
            auth_user,
            "testing",
        )

        # create TOTP with prov uri
        totp = pyotp.parse_uri(resp["data"]["prov_uri"])

        otp = "123456"

        # if this ever happens i will buy a lottery ticket
        if totp.verify(otp):
            otp = "654321"

        # call with wrong OTP
        resp = client.verify_otp_call(
            auth_user,
            "testing",
            otp,
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "OTP incorrect.")

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "setting-up-otp")
        self.assertEqual(stage["username"], "NotExists")

    def test_verify_otp_no_otp(self):
        """
        Tests verifying an OTP when no
        OTP given.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # set password
        _ = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        # setup OTP
        _ = client.setup_otp_call(
            auth_user,
            "testing",
        )

        # call with wrong OTP
        resp_raw = client.call(
            auth_user,
            "testing",
            "verify-otp",
            {},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "setting-up-otp")
        self.assertEqual(stage["username"], "NotExists")

    def test_verify_otp_malformed_otp(self):
        """
        Tests verifying an OTP with too long
        of an OTP.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # set password
        _ = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        # setup OTP
        _ = client.setup_otp_call(
            auth_user,
            "testing",
        )

        # call with wrong OTP
        resp = client.verify_otp_call(
            auth_user,
            "testing",
            "1234567",
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "OTP incorrect.")

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "setting-up-otp")
        self.assertEqual(stage["username"], "NotExists")

    def test_verify_otp_int(self):
        """
        Tests verifying an OTP with an integer
        instead.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # set password
        _ = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        # setup OTP
        resp = client.setup_otp_call(
            auth_user,
            "testing",
        )

        # create TOTP with prov uri
        totp = pyotp.parse_uri(resp["data"]["prov_uri"])

        # call with wrong OTP
        resp = client.verify_otp_call(
            auth_user,
            "testing",
            int(totp.now()),
        )

        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["data"], {})

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "otp-verified")
        self.assertEqual(stage["username"], "NotExists")

    def test_verify_otp_wrong_stage(self):
        """
        Tests verifying an OTP with the wrong
        Valkey stage.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # call with current OTP
        resp = client.verify_otp_call(
            auth_user,
            "testing",
            "123456",
        )

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "username-valid")
        self.assertEqual(stage["username"], "NotExists")

    def test_verify_otp_no_stage(self):
        """
        Tests verifying an OTP with no Valkey
        stage.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())
        resp = client.verify_otp_call(
            auth_user,
            "testing",
            "123456",
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_setup_otp(self):
        """
        Tests setting up an OTP.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # set password
        _ = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        # setup OTP
        resp = client.setup_otp_call(
            auth_user,
            "testing",
        )

        # would throw an error if the uri was invalid
        totp = pyotp.parse_uri(resp["data"]["prov_uri"])

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "setting-up-otp")
        self.assertEqual(stage["username"], "NotExists")
        # check hash still there (would throw KeyError if not)
        _ = stage["hash"]
        self.assertEqual(stage["otp_sec"], totp.secret)

    def test_setup_otp_wrong_stage(self):
        """
        Tests setting up OTP when at wrong stage.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to wrong stage
        # valid username
        auth_user = str(uuid.uuid4())
        _ = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        # setup OTP
        resp = client.setup_otp_call(
            auth_user,
            "testing",
        )

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")

        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        self.assertEqual(stage["stage"], "username-valid")
        self.assertEqual(stage["username"], "NotExists")

    def test_setup_otp_no_stage(self):
        """
        Tests setting up an OTP where the token
        does not have a Valkey stage.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())
        resp = client.setup_otp_call(
            auth_user,
            "testing",
        )

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_token_ttl_set_password(self):
        """
        Tests if a token times out correctly.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())
        stage = json.dumps(
            {
                "stage": "username-valid",
                "username": "NotExists",
            }
        )
        self.vk.setex(f"register:{auth_user}", 1, stage)

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNotNone(vk_stage)

        time.sleep(2)

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

        resp = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_set_password_call(self):
        """
        Tests if the set password helper
        call works.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get token to correct stage
        auth_user = str(uuid.uuid4())
        resp = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["valid"])

        # set password
        resp = client.set_password_call(
            auth_user, "testing", "this-is-a-dummy-value")

        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["data"], {})

        # get valkey stage
        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        # test valkey stage is correct
        self.assertEqual(stage["stage"], "password-set")
        self.assertEqual(stage["username"], "NotExists")
        self.assertFalse(self.ph.check_needs_rehash(stage["hash"]))
        self.assertTrue(self.ph.verify(stage["hash"], "this-is-a-dummy-value"))

    def test_set_password(self):
        """
        Tests if the set password step
        works.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get user to correct stage
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "NotExists"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["valid"])

        # call with dummy already hashed password
        resp_raw = client.call(
            auth_user,
            "testing",
            "set-password",
            {"password-digest": "this-is-a-dummy-value"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["data"], {})

        # get stage from valkey
        stage_raw = self.vk.get(f"register:{auth_user}")
        stage = json.loads(stage_raw)

        # check stage + pw hash
        self.assertEqual(stage["stage"], "password-set")
        self.assertEqual(stage["username"], "NotExists")
        self.assertFalse(self.ph.check_needs_rehash(stage["hash"]))
        self.assertTrue(self.ph.verify(stage["hash"], "this-is-a-dummy-value"))

    def test_set_password_wrong_stage(self):
        """
        Tests that the register service does not
        allow a user to set their password
        until their username has been validated.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # create bad stage
        auth_user = str(uuid.uuid4())
        stage_bad = json.dumps({"stage": "not-a-stage", "username": "foobar"})

        # set stage in valkey
        self.vk.setex(f"register:{auth_user}", 60 * 30, stage_bad)

        # try to set password
        resp_raw = client.call(
            auth_user,
            "testing",
            "set-password",
            {"password-digest": "this-is-a-dummy-value"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 403)
        self.assertEqual(resp["data"]["reason"], "Token not at correct step.")

    def test_set_password_no_stage(self):
        """
        Tests that the register service does
        not allow a user to set their password
        if they have no stage set.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "set-password",
            {"password-digest": "this-is-a-dummy-value"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Token doesn't exist.")

    def test_set_password_no_digest(self):
        """
        Tests that the register service handles
        not being passed a digest correctly.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get user to correct stage
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "NotExists"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["valid"])

        # call with dummy already hashed password
        resp_raw = client.call(
            auth_user,
            "testing",
            "set-password",
            # incorrect field!
            {"password": "this-is-a-dummy-value"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_set_password_blank_digest(self):
        pass

    def test_set_password_bad_digest(self):
        """
        Tests that the register service handles
        not being passed the correct type of
        password digest.
        """
        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # get user to correct stage
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "NotExists"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["valid"])

        # call with dummy already hashed password
        resp_raw = client.call(
            auth_user,
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
        _ = shared.setup_scylla(
            "kc5hm6rrldpq76bbbclsn6s31cdig",
            user=os.environ["SCYLLADB_USERNAME"],
            password=os.environ["SCYLLADB_PASSWORD"],
        )

        models.Accounts.create(
            username="Exists",
        )

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "Exists"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

    def test_check_bad_username(self):
        """
        Tests many cases where the username
        is badly formatted.
        """

        models.Accounts.create(
            username="Exists",
        )

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        # special char in front
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "_user"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

        # special char in back
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "user_"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

        # special char surrounding
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": ".user_"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

        # small username
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "user"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

        # not allowed special char
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "us£rname"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

        # not allowed space
        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "us rname"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertFalse(resp["data"]["valid"])

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

    def test_check_valid_user(self):
        """
        Tests if the check valid user step works
        correctly on unique and valid username.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())
        resp_raw = client.call(
            auth_user,
            "testing",
            "check-valid-username",
            {"username": "NotExists"},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["valid"])

        stage = json.dumps(
            {
                "stage": "username-valid",
                "username": "NotExists",
            }
        )
        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertEqual(stage, vk_stage.decode())

    def test_check_valid_username_call(self):
        """
        Tests the helper RPC call
        for checking for valid username.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        auth_user = str(uuid.uuid4())
        resp = client.check_valid_username_call(
            auth_user,
            "testing",
            "NotExists",
        )

        self.assertEqual(resp["status"], 200)
        self.assertTrue(resp["data"]["valid"])

        stage = json.dumps(
            {
                "stage": "username-valid",
                "username": "NotExists",
            }
        )
        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertEqual(stage, vk_stage.decode())

    def test_check_unique_none(self):
        """
        Tests if the uniue user step
        responds correctly given nothing.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        resp_raw = client.call(
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

        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        resp_raw = client.call("asdfjkl;")
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad JSON.")

    def test_register_malformed(self):
        """
        Tests if the register RPC responds
        correctly to malformed requests.
        """

        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        req = {"hello": "world"}

        resp_raw = client.call(json.dumps(req))
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Malformed request.")

    def test_register_bad_version(self):
        """
        Tests the case where the version
        is not supported.
        """
        client = TestRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "ping-rpc",
        )

        req = rpcs.request(
            "testing",
            "200",
            "testing",
            {"message": "Ping!"},
        )

        resp_raw = client.call(req)
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertRaises(KeyError, lambda x: x["data"]["message"], resp)
        self.assertEqual(resp["data"]["reason"], "Bad version.")

    def test_register_bad_step_type(self):
        """
        Tests the case where the step
        is not the correct type.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc",
        )

        resp_raw = client.call(
            "testing",
            "testing",
            True,
            {},
        )
        resp = json.loads(resp_raw)

        self.assertEqual(resp["status"], 400)
        self.assertEqual(resp["data"]["reason"], "Unknown step.")
