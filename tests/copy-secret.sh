#!/usr/bin/env bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <secret-name> <source-namespace> <destination-namespace>";
    exit 1;
fi

SECRET_NAME="$1"
SOURCE_NAMESPACE="$2"
TARGET_NAMESPACE="$3"

# get the secret data from the source namespace
SECRET_DATA=$(kubectl get secret "$SECRET_NAME" -n "$SOURCE_NAMESPACE" -o jsonpath='{.data}')

# create args for secret recreation
SECRET_ARGS=()
for key in $(echo "$SECRET_DATA" | jq -r 'keys[]'); do
    value=$(echo "$SECRET_DATA" | jq -r ".\"$key\"" | base64 --decode)
    SECRET_ARGS+=("--from-literal=$key=$value")
done

# create the new secret in the target namespace
kubectl create secret generic "$SECRET_NAME" -n "$TARGET_NAMESPACE" "${SECRET_ARGS[@]}"
