#!/bin/bash

set -u

. ./deploy_scripts.cfg

ec2_setup_b64=$(base64 -w0 ec2-setup.sh)
ip_addr=$(curl http://checkip.amazonaws.com)

cat <<EOF > deploy-ec2-params.json
[
    {
        "ParameterKey": "Region",
        "ParameterValue": "${REGION}"
    },
    {
        "ParameterKey": "SSHIp",
        "ParameterValue": "${ip_addr}"
    },
    {
        "ParameterKey": "KeyName",
        "ParameterValue": "${EC2_KEYPAIR_NAME}"
    },
    {
        "ParameterKey": "InstanceTypeParameter",
        "ParameterValue": "${INSTANCE_TYPE}"
    },
    {
        "ParameterKey": "UserData",
        "ParameterValue": "${ec2_setup_b64}"
    }
]
EOF
