from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
import uuid


class Pings(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    message = columns.Text()


class Pongs(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    message = columns.Text()
