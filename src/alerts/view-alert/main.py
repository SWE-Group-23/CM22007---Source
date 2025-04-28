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
        logging.info("trying to view")
        # views all unread alerts for the user
        q = list(models.Alerts.objects.filter(userID=user_id).allow_filtering())
        logging.info("Received q")
        if q:
            unread_q = [a for a in q if not a.read]
            data = {
                "alerts": [
                      {
                           "message": str(alert.message),
                           "service": str(alert.service),
                      }
                      for alert in unread_q
                  ]
            }
            # updating the entries to read

            for alert in unread_q:
                alert.read = True
                alert.save()
            return rpcs.response(200, data)

        logging.error("[DB ERROR] No alerts")
        return rpcs.response(400, {"reason": "No alerts"})

    def process(self, body):
        """
        processing the passed JSON to extract the userID
        """
        try:
            # Loads the data if it is valid JSON
            req = json.loads(body)
        except json.JSONDecodeError:
            return rpcs.response(400, {"reason": "Invalid JSON"})
        try:
           if req["version"] != "1.0.0":
               return rpcs.response(400, {"reason": "Bad version"})

           user_id = req["authUser"]

           res = rpcs.response(500, {"reason": "Internal Server Error"})
           logging.info("calling view_alert")
           res = self.view_alert(user_id)
           return res
        except KeyError:
            return rpcs.response(400, {"reason": "Malformed request."})
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
    logging.info("Consuming...")
    rpc_server.channel.start_consuming()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

