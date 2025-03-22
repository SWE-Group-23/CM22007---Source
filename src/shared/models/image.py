"""Set up tables for profile subsystem."""
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class Image(Model):
    """
    Image table schema:
        img_id - Primary Key (UUID)
        food_id - UUID (food item ID)
        user_id - UUID (uploader's user ID)
        label - Text (descriptive label for the image)
    """
    img_id = columns.UUID(primary_key=True)
    food_id = columns.UUID(required=True)
    user_id = columns.UUID(required=True)
    label = columns.Text()
