"""Set up tables for profile subsystem."""
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class Profile(Model): # pylint: disable=too-few-public-methods
    """
    Profile table:
        username - Primary Key
        profile_pic - UUID
        name - Text
        bio - Text
        food_preferences - Text
        censor - Boolean
    """
    username = columns.Text(primary_key=True)
    profile_pic = columns.UUID()
    name = columns.Text()
    bio = columns.Text()
    food_preferences = columns.Text()
    censor = columns.Boolean(default=False)
