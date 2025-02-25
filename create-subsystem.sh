#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <new-subsystem-name>";
    exit 1;
fi

if [[ ! $1 =~ ^[a-z-]+$ ]]; then
    echo "Subsystem name must only contain lowercase alpha characters and hyphens.";
    exit 2;
fi

if [ ! -d "src/" ]; then
    echo "Source directory not found, please run this script from the repository base directory.";
    exit 3;
fi

DIR="src/$1"

if [[ -d "$DIR" && "$(ls -A $DIR)" ]]; then
    echo "Subsystem directory found and not empty.";
    exit 4;
fi

echo "Creating new subsystem: $1...";
echo "Creating directory $DIR..."
mkdir -p "$DIR"

echo "Creating subsystem ScyllaDB config..."
mkdir -p "$DIR/scylla"
cat >"$DIR/scylla/$1-scylla-perms.yaml" <<EOL
apiVersion: custom.local/v1
kind: ScyllaUser
metadata:
  name: $1-user
spec:
  scyllaClusterReference: dev-db

---

apiVersion: custom.local/v1
kind: ScyllaKeyspace
metadata:
  name: $1-keyspace
spec:
  scyllaClusterReference: dev-db
  replicationFactor: 3

---

apiVersion: custom.local/v1
kind: ScyllaPermission
metadata:
  name: $1-permission
spec:
  scyllaClusterReference: dev-db
  user: $1-user
  keyspace: $1-keyspace
  permission: CREATE
EOL

echo "You should now create services using the create-service.sh script."
