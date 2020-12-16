#!/bin/bash

set -u

. ./deploy_scripts.cfg

aws s3 rb "s3://${DEPLOY_BUCKET}" --profile --force
