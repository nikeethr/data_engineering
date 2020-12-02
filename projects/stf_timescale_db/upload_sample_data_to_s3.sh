#!/bin/sh

# TODO: use cloud formation to do this

set -u

SCRIPT_DIR=$(dirname $(readlink -f $0))
AWS_PROFILE=my-stf-admin
TEST_BUCKET=stf-prototype-sample-data
TEST_DATA="${SCRIPT_DIR}/scripts/stf_ingest/sample_data"
S3_TEST_DATA="s3://${TEST_BUCKET}/sample_data"
REGION=ap-southeast-2

bucket_exists=$(aws s3 ls --profile $AWS_PROFILE | grep -c "${TEST_BUCKET}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${TEST_BUCKET}" \
        --profile $AWS_PROFILE \
        --region $REGION
else
    echo "bucket: ${TEST_BUCKET} already exists. skipping..."
fi

aws s3 sync $TEST_DATA $S3_TEST_DATA --profile $AWS_PROFILE
