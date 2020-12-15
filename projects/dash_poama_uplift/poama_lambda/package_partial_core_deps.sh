#!/bin/bash

set -xu

. ./deploy_scripts.cfg

extra_packages_zip="partial_core_deps.zip"
extra_packages=("numba" "llvmlite")
package_dir="${BUILD_DIR}/ReadNetcdfLayer/python"
s3_bucket=$DEPLOY_BUCKET

pushd $package_dir

echo "zip and remove packages: ${extra_packages[@]}..."
for package in "${extra_packages[@]}"; do
    zip -ur $extra_packages_zip $package
    rm -r $package
done

echo "upload to lambda deploy bucket: ${s3_bucket}..."
bucket_exists=$(aws s3 ls | grep -c "${s3_bucket}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${s3_bucket}" --region $REGION
else
    echo "bucket: ${s3_bucket} already exists. skipping..."
fi

aws s3 cp $extra_packages_zip "s3://${s3_bucket}/extra/${extra_packages_zip}"

echo "clean up..."
rm $extra_packages_zip
popd

