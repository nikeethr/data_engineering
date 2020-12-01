#!/bin/bash

ec2_setup_b64=$(base64 -w0 ec2-setup.sh)
ip_addr=$(curl http://checkip.amazonaws.com)

cat <<EOF > deploy-ec2-params.json
[
    {
        "ParameterKey": "Region",
        "ParameterValue": "ap-southeast-2"
    },
    {
        "ParameterKey": "SSHIp",
        "ParameterValue": "${ip_addr}"
    },
    {
        "ParameterKey": "KeyName",
        "ParameterValue": "stf-ec2-keypair"
    },
    {
        "ParameterKey": "InstanceTypeParameter",
        "ParameterValue": "t2.micro"
    },
    {
        "ParameterKey": "UserData",
        "ParameterValue": "${ec2_setup_b64}"
    }
]
EOF
