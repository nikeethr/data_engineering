#!/bin/bash

set -u

. ./deploy_scripts.cfg

aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION

