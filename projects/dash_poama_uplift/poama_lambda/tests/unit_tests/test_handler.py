import os
import json

import pytest
import logging
from zarr.storage import DirectoryStore

from lambda_plot_nc import app

_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_ZARR_PATH = os.path.join(
    _DIR,
    '../system_tests/test_data/s_moa_sst_20201107_e01.zarr/'
)


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "body": '{ "test": "body"}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {
            "time": "2020-01-03 23:00", "var": "temp"
        },
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "GET",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }


def test_lambda_handler(apigw_event, mocker, monkeypatch, caplog):
    @app._benchmark
    def mock_get_s3_zarr_store():
        store = DirectoryStore(TEST_ZARR_PATH)
        return store

    monkeypatch.setattr(app, "LOCAL_MODE", True)
    monkeypatch.setattr(app, "get_s3_zarr_store", mock_get_s3_zarr_store)

    caplog.set_level(logging.DEBUG, app.LOGGER.name)
    ret = app.lambda_handler(apigw_event, "")

    # second handler to check if time taken is reduced from caching
    apigw_event["queryStringParameters"]["lat_min"] = -60
    apigw_event["queryStringParameters"]["lat_max"] = -40
    apigw_event["queryStringParameters"]["lon_min"] = -90
    apigw_event["queryStringParameters"]["lon_max"] = -50
    ret = app.lambda_handler(apigw_event, "")

    with open(os.path.join(_DIR, 'test.html'), mode="w", encoding="utf-8") as f:
        f.write(ret)
