#!/bin/sh

set -u

. ./deploy_scripts.cfg

# remove test bucket
aws s3 rb "s3://${TEST_BUCKET}" --profile $AWS_PROFILE --force

aws cloudformation delete-stack \
    --stack-name $STACK_NAME \
    --profile $AWS_PROFILE

aws s3 rb "s3://${DEPLOY_BUCKET}" --profile $AWS_PROFILE --force
