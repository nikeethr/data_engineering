#!/bin/bash

. ./deploy_scripts.cfg

default_assets_dir="$(dirname $(readlink -f $0))/assets"
assets_dir=${1:-$default_assets_dir}
s3_bucket=${2:-$PUBLIC_LAMBDA_OUT_BUCKET}

# check if bucket already exists if not make bucket
bucket_exists=$(aws s3 ls | grep -c "${s3_bucket}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${s3_bucket}" --region $REGION
else
    echo "bucket: ${s3_bucket} already exists. skipping..."
fi

# try to upload - objects can be public
aws s3 sync $assets_dir "${s3_bucket}/assets" --acl public-read
