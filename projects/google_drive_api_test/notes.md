- create conda environment for this.
```bash
conda create -n $ENV_NAME python=3
conda activate $ENV_NAME
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
- using service account: https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/service-py
- quick start: https://developers.google.com/drive/api/v3/quickstart/python
- downloading files: https://developers.google.com/drive/api/v3/manage-downloads
- PROTIP: you will need to share your drive with the service account for it to see it.
