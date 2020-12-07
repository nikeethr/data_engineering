#!/bin/sh

set -u

. ./deploy_scripts.cfg

aws s3 rb "s3://${SAMPLE_DATA_BUCKET}" --profile $AWS_PROFILE --force
