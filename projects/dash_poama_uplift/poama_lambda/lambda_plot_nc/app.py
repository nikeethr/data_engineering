# === imports ===
import io
import os
import sys
import dateutil.parser
import functools
import logging
import requests
import time
import uuid
import zipfile
import xarray as xr
import numpy as np
import simplejson
import s3fs
import boto3
from importlib import import_module
from jinja2 import Environment, FileSystemLoader, select_autoescape
from scipy.spatial import KDTree

# delay load datashader as it depends on numba and llvmlite which will be
# loaded on first lambda call
datashader = None

# ===

# ---
# TODO: potentially remove in lambda function
_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_DIR = os.path.join(_DIR, 'templates')
_DATA_OUT = os.path.join(_DIR, 'out', 'data')
_HTML_OUT = os.path.join(_DIR, 'out', 'index.html')
# ---

LOCAL_MODE = False

AWS_PROFILE = os.environ.get('AWS_PROFILE', None)
AWS_REGION = os.environ.get('REGION', 'ap-southeast-2')
S3_ZARR_BUCKET = os.environ.get('S3_ZARR_BUCKET', 'fvt-zarr-data')
S3_OUTPUT_BUCKET = os.environ.get('S3_OUTPUT_BUCKET', 'fvt-lambda-public-data')
S3_DEPLOY_BUCKET = os.environ.get('S3_DEPLOY_BUCKET', 'poama-test-lambda-deploy')
EXTRA_PACKAGES_ZIP = os.environ.get('EXTRA_PACKAGES_ZIP', 'extra/partial_core_deps.zip')
LAMBDA_EXTRA_PACKAGES_PATH = os.environ.get('LAMBDA_EXTRA_PACKAGES_PATH', '/tmp/python_extra/')

jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(['html'])
)

# Keep KD-tree in memory for speedup
KD_TREE_CACHE = None

# === setup logging ===
LOGGER = logging.getLogger(__name__)
log_level = logging.INFO
if LOCAL_MODE:
    log_level = logging.DEBUG
LOGGER.setLevel(log_level)
stream_handler = logging.StreamHandler()
LOGGER.addHandler(stream_handler)
# ===

# === helpers ===

def _benchmark(f):
    """
        Decorator to benchmark the various data processing functions
    """
    # [x] add time profile/logging
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        ts = time.time()
        r = f(*args, **kwargs)
        LOGGER.info('>>> time taken - {}(): {:.3f}s'.format(
            f.__name__, time.time() - ts))
        return r
    return wrapper


@_benchmark
def _prepare_lambda():
    global datashader

    if (os.path.isdir(LAMBDA_EXTRA_PACKAGES_PATH)
            and len(os.listdir(LAMBDA_EXTRA_PACKAGES_PATH)) != 0):
        LOGGER.info("dependencies already downloaded...")
    else:
        LOGGER.info("extracting extra core packages from s3...")
        s3 = s3fs.S3FileSystem(
            anon=False,
            profile=AWS_PROFILE,
            client_kwargs=dict(
                region_name=AWS_REGION,
            )
        )
        with s3.open("{}/{}".format(S3_DEPLOY_BUCKET, EXTRA_PACKAGES_ZIP), 'rb') as s3_obj:
            z = zipfile.ZipFile(io.BytesIO(s3_obj.read()))
            if not os.path.isdir(LAMBDA_EXTRA_PACKAGES_PATH):
                os.makedirs(LAMBDA_EXTRA_PACKAGES_PATH)
            z.extractall(LAMBDA_EXTRA_PACKAGES_PATH)

    sys.path.insert(0, LAMBDA_EXTRA_PACKAGES_PATH)
    
    LOGGER.info("importing datashader...")
    if not datashader:
        datashader = import_module('datashader')

    LOGGER.info("imports successful.")

# ===


# === lambda function ===

def lambda_handler(event, context):
    """
    This function retrieves data from a opendap server and plots the data on a
    map for a give variable at a particular time instance for the given lat/lon
    range.

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    -------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html

    Usage
    -----
    Query Parameters:
        zarr_store [required]: name of zarr file store on s3
        time [required]: time instance
        lat_range [required]: lat slice. comma separated.
        lon_range [required]: lon slice. comma seperated.
        var [required]: variable to plot. So far only supports "temp"

    Example:
        http://<path/to/lambda>/alpha/plot_nc?zarr_store=s_moa_sst_20201107_e01&time=2020-01-05&var=temp&lat_min=50&lat_max=75&lon_min=-50&lon_max=50
    """
    # [x] parse query strings
    # [x] retrieve data from zarr
    # [x] plot the data (or datashsader)
    # [x] log the various stages
    # [ ] if there is an error, raise the error and fail/respond fast

    LOGGER.info("executing lambda function, local_mode = {}".format(LOCAL_MODE))
    ts = time.time()

    operation = event["httpMethod"]
    if operation != "GET":
        return error_response(
            ValueError("Unsupported method '{}'".format(operation)))

    _prepare_lambda()

    try:
        params = extract_params(event["queryStringParameters"])
    except (KeyError, ValueError) as e:
        return error_response(e)

    _, data_uri = get_result_obj_json_uri(params)

    r_exists = requests.get(data_uri, timeout=0.5)
    if r_exists.ok:
        LOGGER.info("data object already created for these params")
        # update params from json
        try:
            data = r_exists.json()
            params['dt'] = data['time']
            params['lon_range'] = data['lon_range']
            params['lat_range'] = data['lat_range']
        except KeyError:
            LOGGER.info("json param keys incorrect - forcing regen...")
            pass
        else:
            pass
            # return make_html_response(params, data_uri)

    store = get_s3_zarr_store(params['zarr_path'])
    res = None

    # Don't chunk for lambda with small CPU - just download and load to memory lazily
    with xr.open_zarr(store, consolidated=True, chunks=None) as ds:
        # if the entire dataset lies within the lat/lon ranges then don't do
        # any kdtree computations.
        if ds_within_lat_lon(params):
            # TODO
            pass
        else:
            # should only run the first time as long as lambda function is
            # warm.
            kdtree = construct_kdtree(ds)

            # get x_2 y_2 range from lat lon range
            x2_range, y2_range = get_x_2_y_2_from_lat_lon(
                ds, params['lon_range'], params['lat_range'])
            LOGGER.info("{}, {}".format(x2_range, y2_range))

            # slice the required data
            da, swapped = slice_dataset(ds, x2_range, y2_range, params)

            # datashader output
            data_uri = rasterize(da, params)

            # make html page
            res = make_html_response(params, data_uri)

    LOGGER.info(">>>> TOTAL TIME TAKEN: {:.3f} s".format(time.time() - ts))

    return res

# ===


# === data procesing functions ===
# TOOD: test if this can go into a separate file(s)

@_benchmark
def get_s3_zarr_store(store_name):
    s3 = s3fs.S3FileSystem(
        anon=False,
        profile=AWS_PROFILE,
        client_kwargs=dict(
            region_name=AWS_REGION,
        )
    )
    store = s3fs.S3Map(root=store_name, s3=s3, check=False)
    return store


def get_result_obj_json_uri(params):
    # using NAMESPACE_URL arbitrarily...
    # but this will create a deterministic name for the json file
    obj_name = str(uuid.uuid3(
        uuid.NAMESPACE_URL,simplejson.dumps(params, default=str)))
    s3_obj_uri = "temp_plot_data/{}.json".format(obj_name)
    s3_uri_external = 'https://s3.{}.amazonaws.com/{}/{}'.format(
        AWS_REGION, S3_OUTPUT_BUCKET, s3_obj_uri)
    return s3_obj_uri, s3_uri_external


@_benchmark
def store_result_json(qm, da, height, width, params):
    out_json = {
        'height': height,
        'width': width,
        'lat': qm.nav_lat.values.astype(np.float16).tolist(),
        'lon': qm.nav_lon.values.astype(np.float16).tolist(),
        'values': qm.values.ravel().astype(np.float16).tolist(),
        'time': str(da.time_counter.item()),
        'lon_range': [int(np.amin(da.nav_lon)), int(np.amax(da.nav_lon))],
        'lat_range': [int(np.amin(da.nav_lat)), int(np.amax(da.nav_lat))],
    }

    s3_obj_uri, uri_external = get_result_obj_json_uri(params)

    # update params before saving html
    params['dt'] = out_json['time']
    params['lon_range'] = out_json['lon_range']
    params['lat_range'] = out_json['lat_range']

    # dump data
    data_str = simplejson.dumps(out_json, ignore_nan=True)
    data_bytes = data_str.encode("utf-8")

    # upload to s3
    session = boto3.Session(region_name=AWS_REGION)
    s3 = session.resource('s3')
    s3_obj = s3.Object(S3_OUTPUT_BUCKET, s3_obj_uri)
    s3_obj.put(
        Body=data_bytes,
        ACL='public-read',
        CacheControl='public, max-age=86400, must-revalidate',
        ContentType='application/json'
    )

    return uri_external
    # ---


@_benchmark
def rasterize(da, params):
    # approximate ratio of the dataframe
    MAX_RES_X = 240
    MAX_RES_Y = 180

    ratio = (da.shape[1] / max(da.shape[0], 1)) * (MAX_RES_Y / MAX_RES_X)

    # to maintain proportional resolution/aspect ratio somewhat
    if ratio < 1:
        width = max(int(MAX_RES_X * ratio), 1)
        height = MAX_RES_Y
    elif ratio > 1:
        width = MAX_RES_X
        height = max(int(MAX_RES_Y / ratio), 1)
    else: # ratio == 1
        width = MAX_RES_X
        height = MAX_RES_Y

    LOGGER.info('datashader canvas - width: {}, height: {}'.format(width, height))
        
    canvas = datashader.Canvas(plot_width=width, plot_height=height)
    qm = canvas.quadmesh(da, x='nav_lon', y='nav_lat')
    data_uri = store_result_json(qm, da, height, width, params)

    return data_uri


@_benchmark
def make_html_response(params, data_uri):
    js_include = 'https://s3.{}.amazonaws.com/{}/{}'.format(
        AWS_REGION, S3_OUTPUT_BUCKET, 'assets/js/main-svg.js')
    css_include = 'https://s3.{}.amazonaws.com/{}/{}'.format(
        AWS_REGION, S3_OUTPUT_BUCKET, 'assets/css/style.css')

    index_template = jinja_env.get_template('index-template.html')

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


@_benchmark
def extract_params(query_params):
    """
        Checks the query string and extracts the relevant parameters raises
        error if something cannot be parsed properly.

        Returns parsed params
    """
    # TODO: load dataset first before updating query params
    dt = dateutil.parser.parse(query_params["time"])
    var = query_params.get("var", "temp")
    # example: <s3_bucket>/zarr/s_moa_sst_20201107_e01.zarr
    zarr_path = "{}/zarr/{}.zarr".format(S3_ZARR_BUCKET, query_params["zarr_store"])
    valid_vars = ["temp"]

    if var not in valid_vars:
        raise KeyError("Invalid var: {}, only accept {}".format(var, valid_vars))

    lat_min = float(query_params.get("lat_min", -90))
    lat_max = float(query_params.get("lat_max", 90))
    lon_min = float(query_params.get("lon_min", -180))
    lon_max = float(query_params.get("lon_max", 180))

    MIN_LATLON = 4

    if np.abs(lat_max - lat_min) <= MIN_LATLON:
        lat_center = (lat_max + lat_min) / 2
        lat_min = int(lat_center - MIN_LATLON / 2)
        lat_max = int(lat_center + MIN_LATLON / 2)

    if np.abs(lon_max - lon_min) <= MIN_LATLON:
        lon_center = (lon_max + lon_min) / 2
        lon_min = int(lon_center - MIN_LATLON / 2)
        lon_max = int(lon_center + MIN_LATLON / 2)

    return {
        "lat_range": [lat_min, lat_max],
        "lon_range": [lon_min, lon_max],
        "var": var,
        "dt": dt,
        "zarr_path": zarr_path,
        "zarr_store": query_params["zarr_store"]
    }


@_benchmark
def construct_kdtree(ds):
    global KD_TREE_CACHE

    if KD_TREE_CACHE is None:
        lat_1d = np.ravel(ds.nav_lat.values)
        lon_1d = np.ravel(ds.nav_lon.values)
        data = np.column_stack((lat_1d, lon_1d))
        # TODO: tweak leaf-size for best construction time/query trade-off
        # No. points is about 1.4e6
        # Note: a lot of points are probably very close to each other so bruteforce
        # for 1000 samples seems okay
        KD_TREE_CACHE = KDTree(data, leafsize=1000)

    return KD_TREE_CACHE


@_benchmark
def get_x_2_y_2_from_lat_lon(ds, lon_range, lat_range):
    t = KD_TREE_CACHE
    if KD_TREE_CACHE is None:
        t = construct_kdtree(ds)

    lon_range_ds = [np.amin(ds.nav_lon), np.amax(ds.nav_lon)]
    lat_range_ds = [np.amin(ds.nav_lat), np.amax(ds.nav_lat)]

    # make sure lon/lat is within range
    lon_range[0] = int(max(lon_range_ds[0], lon_range[0]))
    lon_range[1] = int(min(lon_range_ds[1], lon_range[1]))
    lat_range[0] = int(max(lat_range_ds[0], lat_range[0]))
    lat_range[1] = int(min(lat_range_ds[1], lat_range[1]))

    # construct bounding box in terms of lat/lon
    # -- combining points to potentially improve query speed
    points = [ 
        [lat_range[0], lon_range[0]],
        [lat_range[0], lon_range[1]],
        [lat_range[1], lon_range[0]],
        [lat_range[1], lon_range[1]]
    ]

    # NOTES:
    # `query maps` (lat, lon) -> 1-D index for the kdtree
    # col_size required to convert 1-D indexing to 2-D
    # y_2 = rows, x_2 = col, col_size = len(x_2)

    col_size = ds.nav_lon.shape[1]
    dist, nn = t.query(points, k=5)

    # construct bounding box in the x_2/y_2 space
    points_xy = [
        (int(p / col_size), int(p % col_size))
        for p in nn.ravel()
    ]

    min_x_2 = min([k[1] for k in points_xy])
    max_x_2 = max([k[1] for k in points_xy])
    min_y_2 = min([k[0] for k in points_xy])
    max_y_2 = max([k[0] for k in points_xy])

    y_2_range = [min_y_2, max_y_2]
    x_2_range = [min_x_2, max_x_2]

    return x_2_range, y_2_range


@_benchmark
def ds_within_lat_lon(*args):
    # TODO
    return False


@_benchmark
def slice_dataset(ds, xs, ys, params):
    # TODO: rename this since it's specific slicing for tripolar
    # NOTE: This is very specific to OVT data

    # check if swap required. This is because the dataset switches from -180 to
    # 180 at different points due to the tripolar nature. This will cause
    # issues when plotting.

    # There are two potential ways to select the largest slice:
    #
    # 1. hit 180 -> -180 in between (which could happen if we select any
    # lat/lon that contains the tripole x_2: 266 -> 626)
    # |  ...~... |
    # |  ..~.... |
    # |  .~..... |
    #
    # 2. didn't hit 180 -> -180 transition (e.g. if we select lon 
    # | ..  ~    |
    # | .. ~     |
    # | ..~      |
    #
    # legend:
    # ~ => 180 -> -180
    # . => selected bounding box
    # | => dataset limits (lon) which starts and ends at -75
    # 
    # 2. doesn't need any further processing,
    # for 1. we could instead convert the selection to (which was probably the
    # intended selection anyway):
    # |..  ~   ..|
    # |.. ~    ..|
    # |..~     ..|
    #
    # The way to test for this is if the computed x_2 range from the kd-tree is
    # proportionally similar to the lon range. If it isn't we select:
    # 0 -> x_2[0] and x_2[1] -> max_x_2 instead as per the illustration above.

    da = ds[params['var']].sel(
        time_counter=params['dt'], method="nearest").squeeze()

    n_y, n_x = da.shape
    max_lon = 360 # degrees
    lon_range = params['lon_range']

    lon_diff = np.abs(lon_range[1] - lon_range[0]) / max_lon
    x_diff_noswap = np.abs(xs[1] - xs[0]) / n_x
    x_diff_swap = (n_x - np.abs(xs[1] - xs[0])) / n_x

    if np.abs(x_diff_swap - lon_diff) < np.abs(x_diff_noswap - lon_diff):
        swapped = True
        LOGGER.info("!!! x/y range did not match lat/lon range: swapped dataarray")
        da = xr.concat(
            [
                da[slice(*ys), slice(0, xs[0])].compute(),
                da[slice(*ys), slice(xs[1], None)].compute()
            ],
            dim='x_2'
        )
    else:
        swapped = False
        da = da[slice(*ys), slice(*xs)].compute()

    return da, swapped


@_benchmark
def check_for_lon_discontinuity(xs, swapped):
    """
        If data is discontinuous in longitude true
        This is used to determine if the projection needs to be shifted by 180
    """
    TRIPOLE_RANGE = [266, 626]

    # knowing that tripoles happen between 226 and 626 it's faster to check it
    # this way
    if swapped:
        # Not sure if dicontinuity happens when swapping so set to False if
        # this produces bad artefacts
        dc = xs[0] >= TRIPOLE_RANGE[0] or x[1] < TRIPOLE_RANGE[1]
    else:
        # return true if any one of the x slices cuts through the discontinuity
        # region (note: it may not actually be discontinuous for specific lat
        # ranges but ignoring this for now.)
        dc = ((xs[0] >= TRIPOLE_RANGE[0] and xs[0] < TRIPOLE_RANGE[1])
            or (xs[1] >= TRIPOLE_RANGE[0] and xs[1] < TRIPOLE_RANGE[1]))
    return dc

    # !!! Not used... but potentially useful
    # This is a slower way of doing it
    THRESHOLD = 355  # discontinuity happens from -180 -> 180 => 360 difference
                     # so > 355 is sufficient to capture this.
    a = np.where(da.nav_lon[:, 1:] - da.nav_lon[:, 0:-1] > THRESHOLD)
    return len(a[1]) > 0
    # !!!


def error_response(err):
    """
        Error response to send if something fails. Takes in a Error type.
    """
    # [x] return json format with error message
    return {
        "statusCode": 400,
        "body": str(err),
        "headers": {
            "Content-Type": "application/json"
        }
    }

# ===

