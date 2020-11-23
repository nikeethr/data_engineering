#!/bin/sh

set -u

TEST_BUCKET=fvt-test-zarr-nr
AWS_PROFILE=sam_deploy

aws s3 rb "s3://${DEPLOY_BUCKET}" --profile $AWS_PROFILE --force
