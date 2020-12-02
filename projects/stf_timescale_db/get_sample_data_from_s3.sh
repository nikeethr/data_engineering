#!/bin/bash

set -u

TEST_BUCKET=stf-prototype-sample-data
TEST_DATA="${SCRIPT_DIR}/scripts/stf_ingest/sample_data"
AWS_PROFILE=my-stf-admin

aws s3 sync $S3_TEST_DATA $TEST_DATA --profile $AWS_PROFILE
