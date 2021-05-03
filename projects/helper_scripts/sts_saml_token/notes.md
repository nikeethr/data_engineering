# Rough notes

1. Get SAML code from browser 
  - Get it from developer console for your appropriate browser
  - see: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_saml_view-saml-response.html

> Note: Token must be redeemed within 5 minutes of issuance

2. Run the following command and copy paste the base64 saml-assertion

```sh
aws sts assume-role-with-saml \
  --role-arn arn:aws:iam::ACCOUNTNUMBER:role/IAMROLE \
  --principal-arn arn:aws:iam::ACCOUNTNUMBER:saml-provider/SAMLPROVIDER \
  --saml-assertion BASE64ENCODEDRESPONSE
```

3. Create a profile name and update your credentials with the appropriate
   fields that the previous command outputted. For example:

```
[TEMP_PROFILE]
aws_access_key_id =  ACCESS_KEY_ID
aws_session_token =  SESSION_TOKEN
aws_secret_access_key =  SECRET_ACCESS_KEY
```

> Note: Maximum session duration will be shown in the role - viewable via AWS
> console.

## Helper script

I've created a helper scripts to assist with this.

1. `001_get_temp_credentials.sh`
    - Get the saml response and save it in a file e.g. `saml_response.log`
      (same folder as the script)
    - Update the variables the script to your appropriate role-arn,
      principle-arn and saml-assertion file name.
    - Run the script - this will update your credentials file with the new STS
      token credentials. (It will also create a backup of the original
      credentials file to restore later)
2. `002_test_describe_instances.sh`
    - This is a test command to output details about the EC2 instances
      currently running.
3. `003_cleanup_temp_credentials.sh`
    - This is a simple cleanup script that restores the original credentials
      that has been backed up.

