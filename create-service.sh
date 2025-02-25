#!/usr/bin/env bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <subsystem-name> <new-service-name> <new-service-description>";
    exit 1;
fi

if [[ ! $1 =~ ^[a-z-]+$ ]]; then
    echo "Subsystem name must only contain lowercase alpha characters and hyphens.";
    exit 2;
fi

if [[ ! $2 =~ ^[0-9a-z-]+$ ]]; then
    echo "Service name must only contain lowercase alpha characters, numbers, and hyphens.";
    exit 2;
fi

if [ ! -d "src/" ]; then
    echo "Source directory not found, please run this script from the repository base directory.";
    exit 3;
fi

DIR="src/$1"

if [[ ! -d "$DIR" ]]; then
    echo "Subsystem directory not found, make a subsystem using create-subsystem.sh first.";
    exit 4;
fi

SUB_DIR="$DIR/$2"

if [[ -d "$SUB_DIR" && "$(ls -A $SUB_DIR)" ]]; then
    echo "Service directory found but not empty."
    exit 4;
fi

echo "Creating service..."
mkdir -p "$SUB_DIR";

# Dockerfile
echo "Creating Dockerfile..."
cat >"$SUB_DIR/Dockerfile" <<EOL
FROM python:3.13.1-alpine
COPY --from=ghcr.io/astral-sh/uv:0.5.30 /uv /uvx /bin/

WORKDIR /app
COPY . .

ENV CASS_DRIVER_NO_EXTENSIONS=1

RUN --mount=type=cache,target=/root/.cache/uv \\
    --mount=type=bind,source=uv.lock,target=uv.lock \\
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \\
    uv sync --frozen --no-install-project
    
RUN uv pip install -e shared/

CMD ["uv", "run", "main.py"]
EOL

echo "Creating .dockerignore..."
# .dockerignore
cat >"$SUB_DIR/.dockerignore" <<EOL
.venv/
*.yaml
README.md
EOL

echo "Creating empty README.md..."
# README.md
touch "$SUB_DIR/README.md"

echo "Creating pyproject.toml..."
# pyproject.toml
cat >"$SUB_DIR/pyproject.toml" <<EOL
[project]
name = "$2"
version = "0.1.0"
description = "$3"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "pika>=1.3.2",
    "scylla-driver>=3.28.2",
    "valkey>=6.1.0",
]
EOL

echo "Creating $2.yaml..."
# $2.yaml
cat >"$SUB_DIR/$2.yaml" <<EOL
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $2
  template:
    metadata:
      labels:
        app: $2
    spec:
      containers:
        - name: $2
          image: $2:latest
          imagePullPolicy: IfNotPresent
          tty: true
          env:
            - name: RABBITMQ_USERNAME
              valueFrom:
                secretKeyRef:
                  name: $2-rabbitmq-user-user-credentials
                  key: username
            - name: RABBITMQ_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: $2-rabbitmq-user-user-credentials
                  key: password
            - name: SCYLLADB_USERNAME
              valueFrom:
                secretKeyRef:
                  name: $1-user-scylla-creds
                  key: username
            - name: SCYLLADB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: $1-user-scylla-creds
                  key: password
            - name: SCYLLADB_KEYSPACE
              valueFrom:
                configMapKeyRef:
                  name: $1-keyspace
                  key: keyspace

---

apiVersion: rabbitmq.com/v1beta1
kind: User
metadata:
  name: $2-rabbitmq-user
spec:
  tags:
  - policymaker
  rabbitmqClusterReference:
    name: rabbitmq

---

apiVersion: rabbitmq.com/v1beta1
kind: Permission
metadata:
  name: $2-rabbitmq-permission
spec:
  vhost: "/"
  userReference:
    name: "$2-rabbitmq-user"
  permissions:
    write: ""
    configure: ""
    read: ""
  rabbitmqClusterReference:
    name: rabbitmq
EOL

echo "Creating main.py..."
# main.py
cat >"$SUB_DIR/main.py" <<EOL
"""
Add some service docs here.
"""

import os

import shared
from shared import rpcs

def main():
    """
    Add appropriate docs here.
    """
    raise NotImplementedError

if __name__ == "__main__":
    main()
EOL

echo "Syncing uv dependencies with pyproject.toml..."
(cd "$SUB_DIR"; uv sync)

