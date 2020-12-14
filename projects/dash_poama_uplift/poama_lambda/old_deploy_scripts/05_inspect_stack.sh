#!/bin/sh

set -u

. ./deploy_scripts.cfg

aws cloudformation describe-stacks \
    --profile $AWS_PROFILE \
    --stack-name $STACK_NAME \
    --query 'Stacks[].Outputs' \
    --output table
