"""
Integration tests for the register RPC.
"""

import os
import json
import uuid

import valkey

from lib import AutocleanTestCase
import shared
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

    def __init__(self, methodName, *args, **kwargs):
        super().__init__(methodName, *args, **kwargs)
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

    def test_check_non_unique_user(self):
        """
        Tests if the unique user step works
        correctly on good input.
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
            "register-rpc"
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
        self.assertEqual(resp["data"]["valid"], False)

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
            "register-rpc"
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
        self.assertEqual(resp["data"]["valid"], False)

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
        self.assertEqual(resp["data"]["valid"], False)

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
        self.assertEqual(resp["data"]["valid"], False)

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
        self.assertEqual(resp["data"]["valid"], False)

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
        self.assertEqual(resp["data"]["valid"], False)

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
        self.assertEqual(resp["data"]["valid"], False)

        vk_stage = self.vk.get(f"register:{auth_user}")
        self.assertIsNone(vk_stage)

    def test_check_unique_user(self):
        """
        Tests if the unique user step works
        correctly on bad input.
        """

        client = RegisterRPCClient(
            os.environ["RABBITMQ_USERNAME"],
            os.environ["RABBITMQ_PASSWORD"],
            "register-rpc"
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
        self.assertEqual(resp["data"]["valid"], True)

        stage = json.dumps({
            "stage": "unique",
            "username": "NotExists",
        })
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
            "register-rpc"
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
            "register-rpc"
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

        req = {
            "hello": "world"
        }

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
