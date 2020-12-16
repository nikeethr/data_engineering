#!/bin/sh

set -u

. ./deploy_scripts.cfg

sam logs -n \
    $LAMBDA_FUNC_NAME \
    --region $REGION \
    --stack-name $STACK_NAME --tail
