"""
CQL models for food table.
"""

import uuid

from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Food(Model):  # pylint: disable=too-few-public-methods
    """
    Food Table:
        food_id - UUID - primary key
        user_id - UUID
        img_id - UUID
        label - Text
        useby - DateTime (YYYY-MM-DD'T'HH:MM)
    """
    food_id = columns.UUID(primary_key=True, default=uuid.uuid4())
    user_id = columns.UUID(required=True)
    img_id = columns.UUID()
    label = columns.Text(required=True)
    useby = columns.DateTime(required=True)
