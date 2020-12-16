#!/bin/sh

set -u

. ./deploy_scripts.cfg

aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[].Outputs' \
    --output table \
    --region $REGION
