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
        user1 - Text
        user2 - Text
        blocked - Boolean
    """
    chat_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user1 = columns.Text(index=True)
    user2 = columns.Text(index=True)
    blocked = columns.Boolean(default=False)


class Messages(Model):  # pylint: disable=too-few-public-methods
    """
    Messages table:
        msg_id - UUID - Primary Key
        chat_id - UUID - Partition Key
        sender_user - Text
        sent_time - DateTime
        message - Text
        reported - Boolean
    """
    msg_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    chat_id = columns.UUID(index=True)
    sender_user = columns.Text()
    sent_time = columns.DateTime()
    message = columns.Text()
    reported = columns.Boolean(default=False)
