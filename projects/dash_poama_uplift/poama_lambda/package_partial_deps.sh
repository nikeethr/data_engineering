#!/bin/bash

set -u

s3_bucket=$DEPLOY_BUCKET

# array of packages

# mv packages to temporary folder

# remove unnecessary files

# zip packages

# upload zipped packages to s3
bucket_exists=$(aws s3 ls | grep -c "${s3_bucket}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${s3_bucket}" --region $REGION
else
    echo "bucket: ${s3_bucket} already exists. skipping..."
fi


