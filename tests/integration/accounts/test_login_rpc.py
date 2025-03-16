"""
Integration tests for the login RPC.
"""

from lib import AutocleanTestCase


class LoginRPCTest(AutocleanTestCase):
    """
    Integration tests for the login service
    in the accounts subsystem.
    """

    def setUp(self):  # pylint: disable=invalid-name
        super().setUp()
