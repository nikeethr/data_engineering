#!/bin/bash

# To be run on EC2 instance

set -u

. ./deploy_scripts.cfg

SCRIPT_DIR=$(dirname $(readlink -f $0))
TEST_DATA="${SCRIPT_DIR}/scripts/stf_ingest/sample_data"
S3_TEST_DATA="s3://${SAMPLE_DATA_BUCKET}/sample_data"

aws s3 sync $S3_TEST_DATA $TEST_DATA
