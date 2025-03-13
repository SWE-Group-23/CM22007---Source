"""
Handles the multi-stage registration process.
"""

import os
import json

import valkey

import shared
from shared import rpcs


class RegisterRPCServer(rpcs.RPCServer):
    """
    Serves the register RPC.
    """

    def __init__(self, valkey, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vk = valkey

    def process(self, body):
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            resp = {
                "status": 400,
                "data": {
                    "reason": "Bad JSON."
                },
            }
            return json.dumps(resp)

        try:
            if req["version"] != "1.0.0":
                resp = {
                    "status": 400,
                    "data": {
                        "reason": "Bad version."
                    }
                }
                return json.dumps(resp)

        except KeyError:
            resp = {
                "status": 400,
                "data": {
                    "reason": "Malformed request."
                }
            }
            return json.dumps(resp)





def main():
    """
    Add appropriate docs here.
    """

    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )

    vk = valkey.Valkey(
        host="accounts-valkey",
        port="6379",
        db=0,
        username=os.environ["VALKEY_USERNAME"],
        password=os.environ["VALKEY_PASSWORD"],
    )




    raise NotImplementedError

if __name__ == "__main__":
    main()
