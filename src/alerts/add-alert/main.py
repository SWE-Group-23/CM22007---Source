"""
Adds an alert to the database

To do: set up rpc call and test the code!
"""

import os
import json
import shared
from shared import rpcs

#def addAlert(alertString,userId,alertType,read,async=False):

class AddAlertRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which
    adds an alert
    """

    def add_alert(self, data):
	"""
	Adds the passed alert into the database
	"""

	# adds the alert if all required fields are filled
	user = data.get("authUser")
	if userID is None:
	   return json.dumps(400, {"reason": "No authUser"}

	origin = data.get("from")
	if service is None:
	    return json.dumps(400, {"reason": "No specified origin service"}

	body = data.get("data",{}).get("message")
	if userID is None:
	    return json.dumps(400, {"reason": "No alert"})

	models.Alerts.create(userID=user,message=body,service=origin,read=False)
	return json.dumps(200, {"reason": "alert added succesfully"}


    def process(self, body):
        """
        Respond with "Pong!", unless message
        isn't "Ping!".
        """

	try:
            # Loads the data if it is valid JSON
            data = json.loads(body)
        except json.JSONDecodeError:
            return json.dumps(400, {"reason": "Invalid JSON"})
	return self.add_alert

def main():
    """
    Add appropriate docs here.
    """

    # Set up database session
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # Set up rpcs
    rpc_server = PingRPCServer(
    os.environ["RABBITMQ_USERNAME"],
    os.environ["RABBITMQ_PASSWORD"],
    "add-alert-rpc",
    )

    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    main()









