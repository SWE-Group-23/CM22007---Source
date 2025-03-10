#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <subsystem-name>";
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

if [[ ! -d "$DIR" ]]; then
    echo "Subsystem directory not found.";
    exit 4;
fi

if [[ -d "$DIR/$1-setup-job" && "$(ls -A $DIR/$1-setup-job)" ]]; then
    echo "Setup job directory found but not empty.";
    exit 4;
fi

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
