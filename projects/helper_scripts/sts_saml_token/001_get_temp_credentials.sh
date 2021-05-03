#!/bin/bash

set -eu

SCRIPT_DIR=$(dirname $(readlink -f $0))

# --- CHANGE THESE ---
ROLE_ARN="arn:aws:iam::ACCOUNTNUMBER:role/IAMROLE"
PRINCIPAL_ARN="arn:aws:iam::ACCOUNTNUMBER:saml-provider/SAMLPROVIDER"
# make sure this is unique and different to other profiles
TEMP_PROFILE="TEMP_PROFILE"
SAML_RESPONSE_LOG="${SCRIPT_DIR}/saml_response.log"
# ---

# backup orginal credentials file
cp -a ~/.aws/credentials ~/.aws/credentials.bak

# use aws cli to get the saml role
aws sts assume-role-with-saml \
    --role-arn "${ROLE_ARN}" \
    --principal-arn "${PRINCIPAL_ARN}" \
    --saml-assertion "file://${SAML_RESPONSE_LOG}" | awk -F: '
BEGIN { RS = "[,{}]" ; print "['"${TEMP_PROFILE}"']"}
/:/ { gsub(/"/, "", $2) }
/AccessKeyId/ { print "aws_access_key_id = " $2 }
/SecretAccessKey/ { print "aws_secret_access_key = " $2 }
/SessionToken/ { print "aws_session_token = " $2 }
' >> ~/.aws/credentials

