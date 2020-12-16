#!/bin/sh

set -u

. ./deploy_scripts.cfg

# make s3 bucket for deployment
bucket_exists=$(aws s3 ls --profile $AWS_PROFILE | grep -c "${DEPLOY_BUCKET}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${DEPLOY_BUCKET}" --region $REGION
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
    --capabilities CAPABILITY_IAM \
    --parameter-overrides "DataBucket=${DATA_BUCKET}"`
                        ` "OutputBucket=${PUBLIC_LAMBDA_OUT_BUCKET}"`
                        ` "DeployBucket=${DEPLOY_BUCKET}" `
                        ` "ExtraPackagesZipObj=${EXTRA_PACKAGES_ZIP}"`
                        ` "Region=${REGION}"`
                        ` "LambdaExtraPackagePath=${LAMBDA_EXTRA_PACKAGES_PATH}"
