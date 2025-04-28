"""
CQL models for pings and pongs tables.
"""

import uuid

from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Alerts(Model): # pylint: disable=too-few-public-methods
    """
    Pings table:
        id - UUID - Primary Key
        message - Text
    """
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    userID = columns.Text(index=True)
    message = columns.Text()
    service = columns.Text()
    read = columns.Boolean()
