#!/usr/bin/env bash


if kubectl logs -n testing jobs/testing-service | grep -q "FAILED"; then
    exit 1;
fi

exit 0;
