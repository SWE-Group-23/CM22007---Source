"""
CQL models for food table.
"""

import uuid

from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Food(Model):  # pylint: disable=too-few-public-methods
    """
    Private Food Table:
    userid 
    foodid
    food name - text
    use by date - date
    """
    food_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID()
    label = columns.Text()
    useby = columns.DateTime()
    img_id = columns.UUID()
