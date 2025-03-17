"""
CQL models for pings and pongs tables.
"""

import uuid

from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Pings(Model):  # pylint: disable=too-few-public-methods
    """
    Pings table:
        id - UUID - Primary Key
        message - Text
    """
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    message = columns.Text()


class Pongs(Model):  # pylint: disable=too-few-public-methods
    """
    Pongs table:
        id - UUID - Primary Key
        message - Text
    """
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    message = columns.Text()
