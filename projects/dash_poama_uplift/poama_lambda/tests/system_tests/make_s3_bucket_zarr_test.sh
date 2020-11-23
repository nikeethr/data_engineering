#!/bin/sh

# TODO: use cloud formation to do this

set -u

AWS_PROFILE=sam_deploy
TEST_BUCKET=fvt-test-zarr-nr
REGION=ap-southeast-2

bucket_exists=$(aws s3 ls --profile $AWS_PROFILE | grep -c "${TEST_BUCKET}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${TEST_BUCKET}" \
        --profile $AWS_PROFILE \
        --region $REGION
else
    echo "bucket: ${TEST_BUCKET} already exists. skipping..."
fi
