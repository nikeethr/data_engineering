#!/bin/bash

curl -vX PUT "localhost:5000/v2/awra-base/manifests/awra-base-custom" \
    --data @manifest.json \
    --header "Content-Type: application/vnd.docker.distribution.manifest.v2+json"

