#!/bin/bash

set -eu

# --- CHANGE THESE ---
PROFILE_NAME=TEMP_PROFILE
REGION=ap-southeast-2
# ---

aws ec2 describe-instances \
    --profile "${PROFILE_NAME}" \
    --region "${REGION}"
