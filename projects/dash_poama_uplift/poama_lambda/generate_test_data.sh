#!/bin/sh

set -eu

IMG_TAG="xxx/poama_test_data:1.0"
SCRIPT_DIR=$(dirname $(readlink -f $0))
TEST_DIR="${SCRIPT_DIR}/tests/system_tests"
HOST_TEST_DATA="${TEST_DIR}/test_data/"
CONT_TEST_DATA="/tmp/test_data"

# Generate netcdf files using docker+python and clean up images when done

docker build --rm=true --tag "${IMG_TAG}" "${TEST_DIR}"
docker run \
    --user "$(id -u $USER):$(id -g $USER)" \
    --rm \
    -v "${HOST_TEST_DATA}:${CONT_TEST_DATA}" \
    -v "/etc/passwd:/etc/passwd" \
    -it \
    "${IMG_TAG}"
docker rmi "${IMG_TAG}" --force
