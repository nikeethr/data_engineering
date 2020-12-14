#!/bin/bash

set -eu

. ./deploy_scripts.cfg

script_dir="$(dirname $(readlink -f $0))/scripts"
nc_to_zarr="${script_dir}/netcdf_to_zarr.py"
default_nc_dir="${script_dir}/netcdf_in"
zarr_out="${script_dir}/zarr_out"

# read args if any or use defaults
nc_in=${1:-$default_nc_dir}
s3_bucket=${2:-$DATA_BUCKET}

# convert to zarr
python3 $nc_to_zarr $nc_in $zarr_out

# check if bucket already exists if not make bucket
bucket_exists=$(aws s3 ls | grep -c "${s3_bucket}")

if [ "${bucket_exists}" -eq "0" ]; then
    aws s3 mb "s3://${s3_bucket}" --region $REGION
else
    echo "bucket: ${s3_bucket} already exists. skipping..."
fi

# try to upload
aws s3 sync $zarr_out "${s3_bucket}/zarr"
