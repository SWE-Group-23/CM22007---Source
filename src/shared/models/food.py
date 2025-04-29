"""
CQL models for Food subsystem.
"""

import uuid

from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Food(Model):  # pylint: disable=too-few-public-methods
    """
    Food Table:
        food_id - UUID - primary key
        user - Text - primary key
        img_id - UUID
        label - Text
        description - Text
        useby - DateTime (YYYY-MM-DD'T'HH:MM)
    """
    food_id = columns.UUID(primary_key=True, default=uuid.uuid4())
    user = columns.Text(primary_key=True, index=True)
    img_id = columns.UUID()
    label = columns.Text(required=True)
    description = columns.Text()
    useby = columns.DateTime(required=True)
