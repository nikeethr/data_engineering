#!/bin/sh

set -u

. ./deploy_scripts.cfg

aws cloudformation delete-stack \
    --stack-name $STACK_NAME \
    --profile $AWS_PROFILE

aws s3 rb "s3://${DEPLOY_BUCKET}" --profile $AWS_PROFILE --force
