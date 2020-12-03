#!/bin/sh

set -u

. ./deploy_scripts.cfg

sam logs -n \
    $LAMBDA_FUNC_NAME \
    --profile $AWS_PROFILE \
    --stack-name $STACK_NAME --tail
