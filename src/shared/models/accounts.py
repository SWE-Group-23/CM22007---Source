"""
Defines the table schema for accounts.
"""

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.usertype import UserType


class Suspension(UserType):  # pylint: disable=too-few-public-methods
    """
    UserDefinedType for a suspension instance.
    """
    start = columns.DateTime()
    end = columns.DateTime()
    suspended_by = columns.Text()


class Accounts(Model):  # pylint: disable=too-few-public-methods
    """
    The accounts table schema.
    """
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
    suspension_history = columns.List(columns.UserDefinedType(Suspension))
