"""
Adds a food item to the user's private inventory.
"""

import os

import shared
from shared import rpcs
#from shared import models.food


class CreateFoodRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which creates food items when added.
    """
    def create_food_item(self, user_id, food_name, useby_date):
        """
        Attempts to add a new food item to the user's inventory.
        """
        # user submits info 
        # food name + use by date stored
        # attempts to add to database 
        
        # im behind main
        # try to add to chat table in models
        pass



def main():
    """
    Add appropriate docs here.
    """

    # setup database session 
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # create food rpc
    rpc_server = CreateFoodRPCServer(
       os.environ["RABBITMQ_USERNAME"],
       os.environ["RABBITMQ_PASSWORD"],
    )

    # consuming...
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    main()
