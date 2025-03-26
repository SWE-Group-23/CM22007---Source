"""
CQL models for chats and messages tables.
"""

import uuid

from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Chats(Model):  # pylint: disable=too-few-public-methods
    """
    Chats table:
        chat_id - UUID - Primary Key
        user1 - UUID
        user2 - UUID
        blocked - Boolean
    """
    chat_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user1 = columns.UUID()
    user2 = columns.UUID()
    blocked = columns.Boolean(default=False)


class Messages(Model):  # pylint: disable=too-few-public-methods
    """
    Messages table:
        msg_id - UUID - Primary Key
        chat_id - UUID - Partition Key
        sender_id - UUID
        sent_time - DateTime
        message - Text
        reported - Boolean
    """
    msg_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    chat_id = columns.UUID(index=True)
    sender_id = columns.UUID()
    sent_time = columns.DateTime()
    message = columns.Text()
    reported = columns.Boolean(default=False)
