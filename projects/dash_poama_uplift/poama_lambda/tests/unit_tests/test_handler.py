import os
import simplejson
import sys
import pytest
import logging

_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_ZARR_PATH = os.path.join(
    _DIR,
    '../system_tests/test_data/s_moa_sst_20201107_e01.zarr/'
)
DEPLOY_PACKAGES = os.path.join(_DIR, '../../.aws-sam/build/ReadNetcdfLayer/python')
if os.path.isdir(DEPLOY_PACKAGES):
    sys.path.insert(0, DEPLOY_PACKAGES)

from zarr.storage import DirectoryStore
from lambda_plot_nc import app


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
            "time": "2020-01-03 23:00",
            "var": "temp",
            "zarr_store": "s_moa_sst_20201107_e01"
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
    def mock_get_s3_zarr_store(store_name):
        store = DirectoryStore(TEST_ZARR_PATH)
        return store

    @app._benchmark
    def mock_upload_results_to_s3(out_json):
        with open(os.path.join(app._DATA_OUT, 'ovt_data.json'), 'w') as f:
            simplejson.dump(out_json, f, ignore_nan=True)

    @app._benchmark
    def mock_make_html_response(params, data_uri):
        js_include = 'js/main-canvas.js'
        css_include = 'css/style.css'
        data_uri = 'data/ovt_data.json'

        index_template = app.jinja_env.get_template('index-template.html')

        html_str = index_template.render(
            filename=params['zarr_store'],
            variable=params['var'],
            time=str(params['dt']),
            lat_range=params['lat_range'],
            lon_range=params['lon_range'],
            js_include=js_include,
            css_include=css_include,
            plot_data_url=data_uri
        )

        return {
            "statusCode": 200,
            "body": html_str,
            "headers": {
                "Content-Type": "text/html"
            }
        }


    @app._benchmark
    def mock_prepare_lambda():
        app.LOGGER.info("importing datashader...")
        if not app.datashader:
            app.datashader = app.import_module('datashader')
        app.LOGGER.info("imports successful.")


    monkeypatch.setattr(app, "LOCAL_MODE", True)
    monkeypatch.setattr(app, "_DATA_OUT", os.path.join(_DIR, 'out', 'data'))
    monkeypatch.setattr(app, "_HTML_OUT", os.path.join(_DIR, 'out', 'index.html'))
    monkeypatch.setattr(app, "get_s3_zarr_store", mock_get_s3_zarr_store)
    monkeypatch.setattr(app, "upload_results_to_s3", mock_upload_results_to_s3)
    monkeypatch.setattr(app, "make_html_response", mock_make_html_response)
    monkeypatch.setattr(app, "_prepare_lambda", mock_prepare_lambda)

    caplog.set_level(logging.DEBUG, app.LOGGER.name)
    ret = app.lambda_handler(apigw_event, "")

    # second handler to check if time taken is reduced from caching
    apigw_event["queryStringParameters"]["lat_min"] = -90
    apigw_event["queryStringParameters"]["lat_max"] = 90
    apigw_event["queryStringParameters"]["lon_min"] = -50
    apigw_event["queryStringParameters"]["lon_max"] = 50

    ret = app.lambda_handler(apigw_event, "")
    with open(app._HTML_OUT, 'w') as f:
        f.write(ret['body'])
