#!/bin/sh

set -u

. ./deploy_scripts.cfg

# make s3 bucket for deployment
bucket_exists=$(aws s3 ls --profile $AWS_PROFILE | grep -c "${DEPLOY_BUCKET}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${DEPLOY_BUCKET}" \
        --profile $AWS_PROFILE \
        --region $REGION
else
    echo "bucket: ${DEPLOY_BUCKET} already exists. skipping..."
fi

echo "Changing to build dir: ${BUILD_DIR} and deploying"

cd $BUILD_DIR && \
sam deploy \
    --template-file template.yaml \
    --region $REGION \
    --stack-name $STACK_NAME \
    --s3-bucket $DEPLOY_BUCKET \
    --profile $AWS_PROFILE \
    --capabilities CAPABILITY_IAM
