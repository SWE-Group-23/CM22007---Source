"""
Defines a Valkey credentials operator for creating
new users for each service with permissions
"""

import secrets
from base64 import b64decode
import threading
import sys
import time
import logging

import valkey
from kubernetes import client, config, watch

class ValkeyCredsOperator:
    """
    Valkey credentials operator for creating
    new users for each service with permissions.
    """

    def __init__(self):
        config.load_incluster_config()
        self.api_instance = client.CoreV1Api()
        self.objects_api_instance = client.CustomObjectsApi()

        self.config = {
            "group": "custom.local",
            "version": "v1",
        }

        self.failed = False

        threading.excepthook = self.exit_on_exception

    def exit_on_exception(self, args):
        """
        Handle exceptions.
        """
        self.failed = True
        threading.__excepthook__(args)

    def create_user(self, namespace, name, data):
        """
        Creates a new user in the cluster (if they don't exist),
        also creates a new namespaced secret with
        their credentials.
        """

        logging.info("Creating user: %s.", name)
        logging.info("Using data: %s", str(data))

        password = secrets.token_hex(32)

        su_password = b64decode(
            self.api_instance.read_namespaced_secret(
                data["valkeyClusterReference"], namespace).data["password"]
            ).decode()

        r = valkey.Valkey(
            host=f"{data['valkeyClusterReference']}.{namespace}.svc.cluster.local",
            port="6379",
            db=0,
            username="default",
            password=su_password,
        )

        r.acl_setuser(
                username=name,
                enabled=True,
                passwords="+" + password,
                keys="*",
                commands=data["commands"].split(" ")
        )

        logging.info("Creating secret for user: %s.", name)
        body = client.V1Secret()
        body.string_data = {"username": name, "password": password}
        metadata = client.V1ObjectMeta()
        metadata.name = f"{name}-valkey-creds"
        body.metadata = metadata

        try:
            self.api_instance.create_namespaced_secret(namespace, body)
        except client.exceptions.ApiException as e:
            # 409: conflict, e.g. namespaced secret already exists
            if str(e).find("(409)") == -1:
                raise e
            logging.warning("User secret already exists.")

        del password
        logging.info("Created user: %s.", name)

    def delete_user(self, namespace, name, data):
        """
        Deletes a user in the cluster (if they exist),
        also removing their credentials.
        """
        logging.info("Deleting user: %s", name)
        logging.info("Using data: %s", str(data))

        logging.info("Deleting secret for user %s.", name)


        su_password = b64decode(
            self.api_instance.read_namespaced_secret(
                data["valkeyClusterReference"], namespace).data["password"]
            ).decode()

        r = valkey.Valkey(
            host=f"{data['valkeyClusterNamespace']}.{namespace}.svc.cluster.local",
            port="6379",
            db=0,
            username="default",
            password=su_password,
        )

        r.acl_deluser(name)

        try:
            self.api_instance.delete_namespaced_secret(
                f"{name}-scylla-creds",
                namespace,
            )
        except client.exceptions.ApiException as e:
            # 409: conflict
            if str(e).find("(409)") == -1:
                raise e
            logging.warning("User secret doesn't exist.")

        logging.info("Deleted user: %s.", name)

    def process_users(self):
        """
        Processes user event stream, supports
        creating and deleting users.
        """
        while True:
            stream = watch.Watch().stream(

                self.objects_api_instance.list_cluster_custom_object,
                self.config["group"],
                self.config["version"],
                "valkeyusers",
            )
            for event in stream:
                custom_resource = event['object']
                name = custom_resource['metadata']['name']
                namespace = custom_resource['metadata']['namespace']
                data = custom_resource.get('spec', {})

                match event["type"]:
                    case "ADDED":
                        self.create_user(
                            namespace,
                            name,
                            data,
                        )
                    case "DELETED":
                        self.delete_user(
                            namespace,
                            name,
                            data,
                        )

    def run(self):
        """
        Sets up and runs the operator.
        """

        user_thread = threading.Thread(
            target=self.process_users,
            daemon=True,
        )

        user_thread.start()

        while not self.failed:
            time.sleep(3)

        sys.exit(1)


def main():
    """
    Sets up login, then starts processing
    user, keyspace, and permission streams.
    """
    logging.basicConfig(level=logging.INFO)
    operator = ValkeyCredsOperator()
    operator.run()


if __name__ == "__main__":
    main()
