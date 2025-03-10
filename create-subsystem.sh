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

echo "Creating k8s config directory $DIR/k8s..."
mkdir -p "$DIR/k8s"

echo "Creating k8s namespace config..."
cat >"$DIR/k8s/namespace.yaml" <<EOL
apiVersion: v1
kind: Namespace
metadata:
  name: $1
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted

---

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: $1
spec:
  podSelector: {}
  policyTypes:
  - Ingress

---

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-egress
  namespace: $1
spec:
  podSelector: {}
  policyTypes:
  - Egress
EOL

echo "Creating subsystem ScyllaDB config..."
mkdir -p "$DIR/k8s/scylla"
cat >"$DIR/k8s/scylla/$1-scylla-perms.yaml" <<EOL
apiVersion: custom.local/v1
kind: ScyllaUser
metadata:
  name: $1-user
  namespace: $1
spec:
  scyllaClusterReference: dev-db

---

apiVersion: custom.local/v1
kind: ScyllaKeyspace
metadata:
  name: $1-keyspace
  namespace: $1
spec:
  scyllaClusterReference: dev-db
  replicationFactor: 3

---

apiVersion: custom.local/v1
kind: ScyllaPermission
metadata:
  name: $1-permission
  namespace: $1
spec:
  scyllaClusterReference: dev-db
  user: $1-user
  keyspace: $1-keyspace
  permission: CREATE
EOL

echo "Creating subsystem setup-job..."
mkdir -p "$DIR/$1-setup-job"
cat >"$DIR/$1-setup-job/pyproject.toml" <<EOL
[project]
name = "$1-setup-job"
version = "0.1.0"
description = "Sets up ScyllaDB schema for the subsystem."
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "scylla-driver>=3.28.2",
]
EOL

cat >"$DIR/$1-setup-job/main.py" <<EOL
"""
Sets up ScyllaDB for the subsystem.
"""

import os

import cassandra.cqlengine.management as cm

import shared
from shared.models import template as models


def main():
    """
    Connects to Scylla then ensures table schemas
    are correct.
    """
    _ = shared.setup_scylla(
        keyspace=os.environ["SCYLLADB_KEYSPACE"],
        user=os.environ["SCYLLADB_USERNAME"],
        password=os.environ["SCYLLADB_PASSWORD"],
    )
    
    # sync tables here


if __name__ == "__main__":
    os.environ["CQLENG_ALLOW_SCHEMA_MANAGEMENT"] = "1"
    main()
EOL

cat >"$DIR/$1-setup-job/Dockerfile" <<EOL
FROM python:3.13.1-alpine
COPY --from=ghcr.io/astral-sh/uv:0.5.30 /uv /uvx /bin/

WORKDIR /app
COPY . .

ENV CASS_DRIVER_NO_EXTENSIONS=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project
    
RUN uv pip install -e shared/

RUN addgroup -S group1 && adduser -S user1 -G group1 -u 1000
RUN chown -R user1:group1 /app
USER user1:group1

CMD ["uv", "run", "main.py"]
EOL

cat >"$DIR/$1-setup-job/.dockerignore" <<EOL
.venv/
*.yaml
README.md
.python-version
EOL

cat >"$DIR/$1-setup-job/setup-job.yaml" <<EOL
apiVersion: batch/v1
kind: Job
metadata:
  name: $1-setup-job
  namespace: $1
spec:
  backoffLimit: 1
  template:
    metadata:
      labels:
        app: $1-setup-job
    spec:
      restartPolicy: Never
      containers:
        - name: $1-setup-job
          image: $1-setup-job:latest
          imagePullPolicy: IfNotPresent
          tty: true
          securityContext:
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            runAsUser: 1000
            capabilities:
              drop:
                - ALL
            seccompProfile:
              type: RuntimeDefault
          volumeMounts:
            - mountPath: /home/user1/.cache/uv
              name: uv
            - mountPath: /tmp
              name: temp
          env:
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
      volumes:
        - emptyDir: {}
          name: uv
        - emptyDir: {}
          name: temp
EOL

echo "You should now create services using the create-service.sh script."
