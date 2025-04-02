"""
Adds an alert to the database
"""

import os
import json
import logging
import shared
from shared import rpcs
from shared.models import alerts as models

class AddAlertRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which
    adds an alert
    """
    def __init__(self, rabbitmq_user: str, rabbitmq_pass: str, *, rpc_prefix="add-alert-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)

    def add_alert(self, user, origin, body):
        """
        Adds the passed alert into the database
        """
        logging.info("trying to add")
        # adds the alert if all required fields are filled
        try:

            models.Alerts.create(userID=user,message=body,service=origin,read=False)

            return rpcs.response(200, {"reason": "alert added successfully"})
        except ConnectionError as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
            return rpcs.response(400, {"reason": "Unable to add alert"})

    def process(self, body):
        """
        adds the alert
        """
        logging.info("[RECEIVED] %s", body.decode())

        try:
        # Loads the data if it is valid JSON
            data = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Invalid JSON"})
        logging.info("Decoded JSON: %s", data)
        try:
            if data["version"] != "1.0.0":
                return rpcs.response(400, {"reason": "Bad version."})
            resp = rpcs.response(500, {"reason": "Internal Server Error"})
            user_id = data["authUser"]
            from_svc = data["from"]
            message = data["data"]["message"]

            logging.info("calling add_alert")
            resp = self.add_alert(user_id,from_svc,message)

            return resp
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})

def main():
    """
    Sets up the correct sessions
    """

    # Set up database session
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    # Set up rpcs
    rpc_server = AddAlertRPCServer(
        os.environ["RABBITMQ_USERNAME"],
        os.environ["RABBITMQ_PASSWORD"],
    )
    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
