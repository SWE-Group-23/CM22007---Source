"""
Viewing an alert
"""

import os
import json
import logging

import shared
from shared import rpcs
from shared.models import alerts as models


class ViewAlertRPCServer(rpcs.RPCServer):
    """
    Subclass of RPCServer which
    views an alert
    """

    def __init__(self, rabbitmq_user: str, rabbitmq_pass: str, *, rpc_prefix="view-alert-rpc"):
        super().__init__(rabbitmq_user, rabbitmq_pass, rpc_prefix)


    def view_alert(self, user_id):
        """
        Views the unread alerts for the requesting user
        """

        # views all unread alerts for the user
        try:
            q = models.Alerts.filter(userID=user_id,read=False)
            data = [{"message": str(alert.message),
                    "service": str(alert.service)}
                for alert in q]
           # updating the entries to read
            for alert in q:
                alert.read = True
                alert.update()

            return rpcs.response(200, {"data:", data})
        except q.DoesNotExist as e:
            logging.error("[DB ERROR] %s", e, exc_info=True)
            return rpcs.response(400, {"reason": "Unable to view the alert"})

    def process(self, body):
        """
        processing the passed JSON to extract the userID
        """
        try:
            # Loads the data if it is valid JSON
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Invalid JSON"})
        user_id = req["authUser"]

        res = rpcs.response(500, {"reason": "Internal Server Error"})
        res = self.view_alert(user_id)
        return res

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
    rpc_server = ViewAlertRPCServer(
    os.environ["RABBITMQ_USERNAME"],
    os.environ["RABBITMQ_PASSWORD"],
    )

    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

