import io
import base64
import json
import time
import dateutil.parser
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
import matplotlib.pyplot as plt
import logging
import boto3

# import requests

# TODO: use context to determine if local??
LOCAL_MODE = False

# setup logging
LOGGER = logging.getLogger(__name__)
log_level = logging.INFO
if LOCAL_MODE:
    log_level = logging.DEBUG
LOGGER.setLevel(log_level)
stream_handler = logging.StreamHandler()
LOGGER.addHandler(stream_handler)


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html

    Usage
    -----
    Query Parameters:
        time [required]: format='YYYY-mm-dd' only valid for days in 2020-01
        var [required]: 'precipitation' or 'temperature'
        x0 [optional]: lower limit of x axis
        x1 [optional]: upper limit of x axis
        y0 [optional]: lower limit of y axis
        y1 [optional]: upper limit of y axis

    Example:
        http://<path/to/lambda>/alpha/plot_nc??time=2020-01-05&var=precipitation&x0=10
    """

    # try:
    #     ip = requests.get("http://checkip.amazonaws.com/")
    # except requests.RequestException as e:
    #     # Send some context about this error to Lambda Logs
    #     print(e)
    #     raise e

    LOGGER.info("executing lambda function, local_mode = {}".format(LOCAL_MODE))

    # --- process incoming request ---

    operation = event["httpMethod"]

    if operation != "GET":
        return respond(ValueError("Unsupported method '{}'".format(operation)))

    LOGGER.debug(json.dumps(event, indent=4))

    try:
        plot_params = get_plot_params(event["queryStringParameters"])
    except (ValueError, KeyError) as e:
        LOGGER.exception(e)
        return respond(e)

    LOGGER.debug(json.dumps(plot_params, indent=4, default=str))


    # --- grab/generate dataset ---
    if LOCAL_MODE:
        LOGGER.info("Generating dataset...")
        ds = local_generate_ds()
    else:
        LOGGER.info("Grabbing dataset from s3...")
        ds = get_ds_s3()

    LOGGER.info("Plotting image...")


    # --- generate image ---
    try:
        img = sample_plot(
            ds,
            xs=[plot_params['x0'], plot_params['x1']],
            ys=[plot_params['y0'], plot_params['y1']],
            var=plot_params["var"],
            time_=plot_params["time"]
        )
    except KeyError as e:
        LOGGER.exception(e)
        return respond(e)

    LOGGER.info("Preparing response...")

    # ---
    # FOR REQUESTS with explicity Accept-Header = "image/png"
    # uncomment line below returning image directly. Wasn't able to get this to
    # work with browsers but will work with: `curl -H "Accept: image/png"`
    # ---
    # return respond(None, res=img, content_type="image/png", base_64=True)

    # ---
    # FOR RESPONDING TO BROWSERS:
    # below works better for browsers but you can't download image directly:
    # ---
    img_html = local_img_html(img)
    return respond(None, res=img_html, content_type="text/html")


def get_ds_s3():
    # TODO: use `s3fs` instead of this as it may handle things better
    start_t = time.time()

    BUCKET_NAME = "sam-poama-netcdf-test-data"
    OBJ_TEST_DATA = "test_data/poama_lambda_test_data.nc"

    session = boto3.Session()
    s3 = session.client('s3')

    nc_buffer = io.BytesIO()
    s3.download_fileobj(BUCKET_NAME, OBJ_TEST_DATA, nc_buffer)
    nc_buffer.seek(0)

    ds = xr.load_dataset(nc_buffer)

    delta_t = time.time() - start_t
    LOGGER.debug(ds)
    LOGGER.info("Successfully retrieved dataset from S3.")
    LOGGER.info("--- [get_ds_s3] time taken: {:.2f}s ---".format(delta_t))

    return ds


def get_plot_params(query_string_params):
    if not query_string_params:
        raise KeyError("Required query parameters: {}".format(["time", "var"]))

    time_ = dateutil.parser.parse(query_string_params["time"])
    var = query_string_params["var"]
    x0 = int(query_string_params.get("x0", 0))
    x1 = int(query_string_params.get("x1", 100))
    y0 = int(query_string_params.get("y0", 0))
    y1 = int(query_string_params.get("y1", 100))

    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0

    valid_vars = ["temperature", "precipitation"]

    if var not in valid_vars:
        raise KeyError("Invalid var: {}, only accept {}".format(var, valid_vars))

    return { "x0": x0, "x1": x1, "y0": y0, "y1": y1, "time": time_, "var": var }


def respond(err, res=None, content_type=None, base_64=False):
    if content_type is None:
        content_type = "application/json"

    if err is not None:
        res = str(err)
        status_code = 400
    else:
        status_code = 200
        
    # TODO: caching if image e.g. - Cache-Control: private, max-age=604800
    return {
        "statusCode": status_code,
        "body": res,
        "headers": {
            "Content-Type": content_type,
        },
        "isBase64Encoded": base_64
    }


def sample_plot(ds, xs, ys, var, time_):
    """
        ds   - xarray.Dataset  - dataset containing data to plot
        xs   - (int, int)      - lower and upper bound of x to plot
        ys   - (int, int)      - lower and upper bound of y to plot
        var  - str             - temperature or precipitation
        time_ - str             - time slice to choose YYYY-mm-dd
    """
    start_t = time.time()
    # select data - this will come from http response
    da = ds[var]

    # bound shape to data size
    xs[0] = int(np.max([xs[0], 0]))
    xs[1] = int(np.min([xs[1], da.shape[0]-1]))
    ys[0] = int(np.max([ys[0], 0]))
    ys[1] = int(np.min([ys[1], da.shape[1]-1]))

    da = da.sel(
        x=slice(xs[0],xs[1]),
        y=slice(ys[0],ys[1]),
        time=time_.strftime("%Y-%m-%d")
    )

    # plot heatmap
    # plt.imshow(da.T)
    heatmap = plt.pcolor(da.T)

    # legend
    plt.colorbar(heatmap)

    # layout
    plt.xticks(range(0, da.shape[0], 5), da["x"].values[range(0, da.shape[0], 5)])
    plt.yticks(range(0, da.shape[1], 5), da["y"].values[range(0, da.shape[1], 5)])
    plt.subplots_adjust(left=0.15, right=0.99, bottom=0.15, top=0.90)

    # labels
    plt.ylabel("Y")
    plt.xlabel("X")
    plt.title("{} - {}".format(var, time_))

    # save figure into response
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close("all")

    # --- binary to base64 ---
    # NOTE: for lambda to work with binary base64 encoded data -
    # you will have to manually enable this:
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/lambda-proxy-binary-media.html
    img64 = base64.b64encode(img_buffer.getvalue())

    delta_t = time.time() - start_t
    LOGGER.info("Successfully plotted image.")
    LOGGER.info("--- [sample_plot] time taken: {:.2f}s ---".format(delta_t))

    return img64


# For testing purposes only - this will not be needed when deployed to API
# gateway. Note: alternative way is to setup public s3 storage to show the
# image
def local_img_html(img):
    prefix = "data:image/png;base64,"
    img_str = img.decode("utf-8").replace("\n", "")
    html = """
<html>
    <head><title>Some lambda test</title></head>
    <body><img src=\"{}\"></img></body>
</html>
""".format(prefix + img_str)
    return html


def local_generate_ds():
    start_t = time.time()

    N_T=30
    N_X=100
    N_Y=100

    temp = 15 + 8 * np.random.rand(N_X, N_Y, N_T)
    precip = 10 * np.random.rand(N_X, N_Y, N_T)

    ds = xr.Dataset(
        {
            "temperature": (["x", "y", "time"], temp),
            "precipitation": (["x", "y", "time"], precip)
        },
        coords={
            "x": np.arange(0, N_X),
            "y": np.arange(0, N_Y),
            "time": pd.date_range("2020-01-01", periods=30)
        }
    )

    delta_t = time.time() - start_t
    LOGGER.info("Successfully generated dataset.")
    LOGGER.info("--- [local_generate_ds] time taken: {:.2f}s ---".format(delta_t))

    return ds

