#!/bin/bash

# To be run on EC2 instance

set -u

SCRIPT_DIR=$(dirname $(readlink -f $0))
TEST_BUCKET=stf-prototype-sample-data
TEST_DATA="${SCRIPT_DIR}/scripts/stf_ingest/sample_data"

aws s3 sync $S3_TEST_DATA $TEST_DATA
