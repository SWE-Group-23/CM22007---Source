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

    def _get_su_password(self, namespace, data):
        """
        Retrieves the superuser password.
        """
        cluster_name = data["valkeyClusterReference"]
        try:
            su_secret = self.api_instance.read_namespaced_secret(
                cluster_name, namespace
            )
            return b64decode(su_secret.data["password"]).decode()
        except client.exceptions.ApiException as e:
            logging.error(
                "Failed to read superuser secret %s: %s", cluster_name, e)
            raise e

    def _create_or_update_user_secret(self, namespace, name, data, password):
        """
        Creates or updates a secret with the user's credentials.
        """
        secret_name = f"{name}-valkey-creds"
        body = client.V1Secret()
        body.string_data = {
            "username": name,
            "password": password,
        }
        metadata = client.V1ObjectMeta(
            name=secret_name,
            labels={
                "app.kubernetes.io/component": "valkey",
                "app.kubernetes.io/instance": data["valkeyClusterReference"],
            },
        )
        body.metadata = metadata

        try:
            self.api_instance.create_namespaced_secret(namespace, body)
            logging.info("Created secret for user %s.", name)
        except client.exceptions.ApiException as e:
            if e.status == 409:
                # Update existing secret
                existing_secret = self.api_instance.read_namespaced_secret(
                    secret_name, namespace
                )
                existing_secret.string_data = body.string_data
                self.api_instance.replace_namespaced_secret(
                    secret_name, namespace, existing_secret
                )
                logging.info("Updated secret for user %s.", name)
            else:
                raise e

    def create_user(self, namespace, name, data):
        """
        Creates or updates a user in Valkey and ensures the secret is updated.
        """
        logging.info("Creating/updating user: %s.", name)
        logging.info("Using data: %s", str(data))

        su_password = self._get_su_password(namespace, data)

        # start handling update
        secret_name = f"{name}-valkey-creds"
        user_password = None

        # check for existing user secret
        try:
            user_secret = self.api_instance.read_namespaced_secret(
                secret_name, namespace
            )
            # if exists, then use password from current secret
            user_password = b64decode(user_secret.data["password"]).decode()
            logging.info(
                "Using existing password for user %s from secret.", name)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                # if it doesn't exist, generate new password
                user_password = secrets.token_hex(32)
                logging.info("Generated new password for user %s.", name)
                self._create_or_update_user_secret(
                    namespace, name, data, user_password)
            else:
                raise e

        # configure user
        cluster_name = data["valkeyClusterReference"]
        r = valkey.Valkey(
            host=f"{cluster_name}.{namespace}.svc.cluster.local",
            port=6379,
            username="default",
            password=su_password,
        )

        # check if the user exists
        try:
            _ = r.acl_getuser(name)
            user_exists = True
        except valkey.exceptions.ResponseError as e:
            if "User " + name + " does not exist" in str(e):
                user_exists = False
            else:
                raise e

        # create or update user password
        if user_exists:
            logging.info("Updating existing user %s.", name)
            r.acl_setuser(
                username=name,
                enabled=True,
                passwords=[f"+{user_password}"],
                reset_passwords=True,
                keys="*",
                commands=data["commands"].split(" "),
            )
        else:
            logging.info("Creating new user %s.", name)
            r.acl_setuser(
                username=name,
                enabled=True,
                passwords=[f"+{user_password}"],
                keys="*",
                commands=data["commands"].split(" "),
            )

        # ensure secret is up to date
        try:
            current_secret = self.api_instance.read_namespaced_secret(
                secret_name, namespace
            )
            current_password = b64decode(
                current_secret.data["password"]).decode()
            if current_password != user_password:
                self._create_or_update_user_secret(
                    namespace, name, data, user_password)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                self._create_or_update_user_secret(
                    namespace, name, data, user_password)
            else:
                raise e

        logging.info("User %s configured successfully.", name)
        r.close()

    def delete_user(self, namespace, name, data):
        """
        Deletes a user in the cluster (if they exist),
        also removing their credentials.
        """

        logging.info("Deleting user: %s", name)
        logging.info("Using data: %s", str(data))

        # retrieve superuser password
        su_password = self._get_su_password(namespace, data)

        cluster_name = data["valkeyClusterReference"]
        r = valkey.Valkey(
            host=f"{cluster_name}.{namespace}.svc.cluster.local",
            port=6379,
            username="default",
            password=su_password,
        )

        # delete user
        try:
            r.acl_deluser(name)
            logging.info("Deleted user %s from Valkey.", name)
        except valkey.exceptions.ResponseError as e:
            if "User " + name + " does not exist" not in str(e):
                raise e

        # delete secret
        secret_name = f"{name}-valkey-creds"
        try:
            self.api_instance.delete_namespaced_secret(secret_name, namespace)
            logging.info("Deleted secret for user %s.", name)
        except client.exceptions.ApiException as e:
            if e.status != 404:
                raise e

        r.close()

    def process_users(self):
        """
        Processes user event stream for create/update/delete events.
        """
        w = watch.Watch()
        while True:
            stream = w.stream(
                self.objects_api_instance.list_cluster_custom_object,
                self.config["group"],
                self.config["version"],
                "valkeyusers",
            )
            for event in stream:
                cr = event["object"]
                name = cr["metadata"]["name"]
                namespace = cr["metadata"]["namespace"]
                data = cr.get("spec", {})

                event_type = event["type"]
                logging.info("Handling event %s for user %s", event_type, name)

                try:
                    if event_type in ("ADDED", "MODIFIED"):
                        self.create_user(namespace, name, data)
                    elif event_type == "DELETED":
                        self.delete_user(namespace, name, data)
                except Exception as e:
                    logging.error("Error processing event: %s", e)
                    self.failed = True
                    raise

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
    Sets up logging, then runs the operator.
    """
    logging.basicConfig(level=logging.INFO)
    operator = ValkeyCredsOperator()
    operator.run()


if __name__ == "__main__":
    main()
