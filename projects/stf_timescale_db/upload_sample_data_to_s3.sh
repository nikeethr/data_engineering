#!/bin/sh

# TODO: use cloud formation to do this

set -u

. ./deploy_scripts.cfg

SCRIPT_DIR=$(dirname $(readlink -f $0))
TEST_DATA="${SCRIPT_DIR}/scripts/stf_ingest/sample_data"
S3_TEST_DATA="s3://${SAMPLE_DATA_BUCKET}/sample_data"

bucket_exists=$(aws s3 ls --profile $AWS_PROFILE | grep -c "${SAMPLE_DATA_BUCKET}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${SAMPLE_DATA_BUCKET}" \
        --profile $AWS_PROFILE \
        --region $REGION
else
    echo "bucket: ${SAMPLE_DATA_BUCKET} already exists. skipping..."
fi

aws s3 sync $TEST_DATA $S3_TEST_DATA --profile $AWS_PROFILE
