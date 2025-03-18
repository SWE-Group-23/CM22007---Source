#!/usr/bin/env bash

TEST_STATUS=$(kubectl get job testing-service -n testing -o jsonpath='{.status.succeeded}')
POD_NAME=$(kubectl get pods -n testing -l job-name=testing-service -o jsonpath='{.items[0].metadata.name}')

if [ -z "$$POD_NAME" ]; then
    echo "Error: Could not find pod associated with job 'testing-service'.";
    exit 1;
fi

kubectl logs -n testing $POD_NAME
