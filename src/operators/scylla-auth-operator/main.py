"""
ScyllaDB credentials operator for creating
new users for each service with permissions
only in their own keyspace.
"""


import secrets
from base64 import b32hexencode
import threading
import sys
import os
import time
from functools import partial

from kubernetes import client, config, watch
import cassandra.cluster as cc
import cassandra.auth as ca
import cassandra as cs

config.load_incluster_config()
api_instance = client.CoreV1Api()
objects_api_instance = client.CustomObjectsApi()

group = "custom.local"
namespace = "default"
version = "v1"

failed = False

db_username = "cassandra"
db_password = "cassandra"


def exit_on_exception(args):
    """
    Handle exceptions.
    """
    global failed

    failed = True

    threading.__excepthook__(args)


threading.excepthook = exit_on_exception


def cluster_connect(contact_points):
    """
    Connects to a cluster with given
    contact points, returing
    a session.
    """
    cluster = cc.Cluster(
        contact_points=contact_points,
        auth_provider=ca.PlainTextAuthProvider(
            username=db_username,
            password=db_password,
        )
    )

    return cluster.connect()


def setup_login():
    """
    Sets up.
    """
    global db_username
    global db_password

    env = os.environ

    if "DB_USERNAME" in env and "DB_PASSWORD" in env:
        db_username = env["DB_USERNAME"]
        db_password = env["DB_PASSWORD"]
        return

    session = cluster_connect(["example-db-client.scylla.svc"])

    db_username = "su" + secrets.token_hex(20)
    db_password = secrets.token_hex(32)

    session.execute(
        """
        CREATE ROLE %s WITH SUPERUSER = true
        AND LOGIN = true AND PASSWORD = %s;
        """,
        (db_username, db_password)
    )

    body = client.V1Secret()
    body.string_data = {"username": db_username, "password": db_password}
    metadata = client.V1ObjectMeta()
    metadata.name = "example-db-superuser"
    body.metadata = metadata

    api_instance.create_namespaced_secret(namespace, body)

    session = cluster_connect(["example-db-client.scylla.svc"])

    session.execute(
        """
        DROP ROLE cassandra;
        """
    )


def create_user(namespace, name, data):
    """
    Creates a new user in the cluster (if they don't exist),
    also creates a new namespaced secret with
    their credentials.
    """
    print(f"user: {name} created!")
    print(name)
    print(data)

    session = cluster_connect(
        [f"{data['scyllaClusterReference']}-client.scylla.svc"]
    )

    password = secrets.token_hex(32)

    session.execute(
        "CREATE USER IF NOT EXISTS %s WITH PASSWORD %s;",
        (name, password,)
    )

    body = client.V1Secret()
    body.string_data = {"username": name, "password": password}
    metadata = client.V1ObjectMeta()
    metadata.name = f"{name}-user-creds"
    body.metadata = metadata

    try:
        api_instance.create_namespaced_secret(namespace, body)
    except client.exceptions.ApiException as e:
        # 409: conflict, e.g. namespaced secret already exists
        if str(e).find("(409)") == -1:
            raise e

    del password


def delete_user(namespace, name, data):
    """
    Deletes a user in the cluster (if they exist),
    also removing their credentials.
    """
    print(f"user: {name} deleted!")

    session = cluster_connect(
        [f"{data['scyllaClusterReference']}-client.scylla.svc"]
    )

    session.execute("DROP USER IF EXISTS %s;", (name,))

    try:
        api_instance.delete_namespaced_secret(f"{name}-user-creds", namespace)
    except client.exceptions.ApiException as e:
        # 409: conflict
        if str(e).find("(409)") == -1:
            raise e


def process_users():
    """
    Processes user event stream, supports
    creating and deleting users.
    """
    while True:
        stream = watch.Watch().stream(
            objects_api_instance.list_namespaced_custom_object,
            group, version, namespace, "scyllausers",
        )
        for event in stream:
            custom_resource = event['object']
            name = custom_resource['metadata']['name']
            data = custom_resource.get('spec', {})

            match event["type"]:
                case "ADDED":
                    create_user(namespace, name, data)
                case "DELETED":
                    delete_user(namespace, name, data)


def encode_keyspace_name(name):
    """
    Encodes a keyspace name as:
        k<base64-name>

    with base64 padding (=) replaced
    with underscores (_)
    """
    return "k" + b32hexencode(name.encode()).decode().replace("=", "_")


def create_keyspace(_namespace, name, data):
    """
    Creates a keyspace for a user.
    """
    session = cluster_connect(
        [f"{data['scyllaClusterReference']}-client.scylla.svc"]
    )

    keyspace_name = encode_keyspace_name(name)

    session.execute(
        """
        CREATE KEYSPACE IF NOT EXISTS """ + keyspace_name + """
            WITH REPLICATION = {
                'class': 'SimpleStrategy',
                'replication_factor': %s
            }
            AND DURABLE_WRITES = true;
        """,
        (data["replicationFactor"],)
    )

    print(f"keyspace {name} created!")
    print(name)
    print(data)
    print(keyspace_name)


def delete_keyspace(_namespace, name, data):
    """
    Deletes a keyspace for a user.
    """
    print(f"keyspace {name} deleted")

    session = cluster_connect(
        [f"{data['scyllaClusterReference']}-client.scylla.svc"]
    )

    keyspace_name = encode_keyspace_name(name)

    session.execute(
        f"""
        DROP KEYSPACE {keyspace_name};
        """
    )


def process_keyspaces():
    """
    Processes keyspace event stream,
    supports creating and deleting
    keyspaces.
    """
    while True:
        stream = watch.Watch().stream(
            objects_api_instance.list_namespaced_custom_object,
            group, version, namespace, "scyllakeyspaces",
        )
        for event in stream:
            custom_resource = event['object']
            name = custom_resource['metadata']['name']
            data = custom_resource.get('spec', {})

            match event["type"]:
                case "ADDED":
                    create_keyspace(namespace, name, data)
                case "DELETED":
                    delete_keyspace(namespace, name, data)


def create_permission(_namespace, name, data):
    """
    Grants all permissions to a specific
    user in their keyspace.
    """
    print(f"permision {name} created!")
    print(name)
    print(data)

    session = cluster_connect(
        [f"{data['scyllaClusterReference']}-client.scylla.svc"]
    )

    keyspace_name = encode_keyspace_name(
        data["keyspace"]
    )

    assert data["permission"].upper() in [
        "ALL", "CREATE", "ALTER", "DROP",
        "SELECT", "MODIFY", "AUTHORIZE", "DESCRIBE"
    ]

    while True:
        try:
            session.execute(
                f"""
                GRANT {data["permission"]} ON KEYSPACE {keyspace_name} TO %s
                """,
                (data["user"],)
            )
            break
        except cs.InvalidRequest as e:
            if str(e).find("doesn't exist") == -1:
                raise e

            print("Couldn't create permission. Retrying")
            time.sleep(5)
            continue


def delete_permission(_namespace, name, data):
    """
    Revokes permissions from a user
    in their keyspace.
    """
    print(f"permission {name} deleted")

    session = cluster_connect(
        [f"{data['scyllaClusterReference']}-client.scylla.svc"]
    )

    keyspace_name = encode_keyspace_name(data["keyspace"])

    assert data["permission"].upper() in [
        "ALL", "CREATE", "ALTER", "DROP",
        "SELECT", "MODIFY", "AUTHORIZE", "DESCRIBE"
    ]

    while True:
        try:
            session.execute(
                f"""
                REVOKE {data["permission"]}
                ON KEYSPACE {keyspace_name}
                FROM %s;
                """,
                (data["user"],)
            )
            break
        except cs.InvalidRequest as e:
            if str(e).find("doesn't exist") == -1:
                raise e

            print("Couldn't delete permission. Retrying")
            time.sleep(5)
            continue


def process_permissions():
    """
    Processes permissions event stream,
    supports granting and revoking
    permissions from users in their
    keyspaces.
    """
    while True:
        stream = watch.Watch().stream(
            objects_api_instance.list_namespaced_custom_object,
            group, version, namespace, "scyllapermissions",
        )
        for event in stream:
            custom_resource = event['object']
            name = custom_resource['metadata']['name']
            data = custom_resource.get('spec', {})

            match event["type"]:
                case "ADDED":
                    job = threading.Thread(
                        target=partial(
                            create_permission,
                            namespace,
                            name,
                            data,
                        )
                    )
                    job.start()
                case "DELETED":
                    job = threading.Thread(
                        target=partial(
                            delete_permission,
                            namespace,
                            name,
                            data,
                        )
                    )
                    job.start()


def main():
    """
    Sets up login, then starts processing
    user, keyspace, and permission streams.
    """
    setup_login()

    user_thread = threading.Thread(
        target=process_users,
        daemon=True,
    )

    keyspace_thread = threading.Thread(
        target=process_keyspaces,
        daemon=True,
    )

    permission_thread = threading.Thread(
        target=process_permissions,
        daemon=True,
    )

    user_thread.start()
    keyspace_thread.start()
    permission_thread.start()

    while not failed:
        time.sleep(3)

    sys.exit(1)


if __name__ == "__main__":
    main()
