# === imports ===
import sys
sys.path.append("/tmp/python_packages")
import os
import time
import dateutil.parser
import functools
import json
import logging
import xarray as xr
import numpy as np
import datashader
import simplejson
import s3fs
from jinja2 import Environment, FileSystemLoader, select_autoescape
from scipy.spatial import KDTree
from datashader import transfer_functions as tf

# ===

# ---
# TODO: potentially remove in lambda function
_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_DIR = os.path.join(_DIR, 'templates')
_DATA_OUT = os.path.join(_DIR, 'out', 'data')
_HTML_OUT = os.path.join(_DIR, 'out', 'index.html')
# ---

LOCAL_MODE = False

AWS_PROFILE = 'sam_deploy'
AWS_REGION = 'ap-southeast-2'
S3_ZARR_STORE = 'fvt-test-zarr-nr/test_zarr_store.zarr'

jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(['html'])
)


# TODO:
# can be same bucket - can setup lifecycle rule to do this as well:
# S3_PLOT_DATA
# S3_PAGE_TEMPLATE

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
        time [required]: time instance
        lat_range [required]: lat slice. comma separated.
        lon_range [required]: lon slice. comma seperated.
        var [required]: variable to plot. So far only supports "temp"

    Example:
        http://<path/to/lambda>/alpha/plot_nc??time=2020-01-05&var=temp&lat_range=50,75&lon_range=-50,50
    """
    # [x] parse query strings
    # [x] retrieve data from zarr
    # [ ] plot the data (or datashsader)
    # [ ] log the various stages
    # [ ] if there is an error, raise the error and fail/respond fast

    LOGGER.info("executing lambda function, local_mode = {}".format(LOCAL_MODE))

    operation = event["httpMethod"]
    if operation != "GET":
        return error_response(
            ValueError("Unsupported method '{}'".format(operation)))

    ts = time.time()
    params = extract_params(event["queryStringParameters"])
    LOGGER.debug(json.dumps(params, indent=4, default=str))

    store = get_s3_zarr_store()

    res = None

    with xr.open_zarr(store, consolidated=True) as ds:
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
            LOGGER.debug("lon: {}, lat: {}".format(
                [np.min(ds.nav_lon.values), np.max(ds.nav_lon.values)],
                [np.min(ds.nav_lat.values), np.max(ds.nav_lat.values)]
            ))
            x2_range, y2_range = get_x_2_y_2_from_lat_lon(
                ds, params['lon_range'], params['lat_range'])
            LOGGER.debug("{}, {}".format(x2_range, y2_range))

            # slice the required data
            da, swapped = slice_dataset(ds, x2_range, y2_range, params)

            # datashader output
            data_uri = rasterize(da)

            # make html page
            res = make_html_page(params, data_uri)

    LOGGER.info(">>>> TOTAL TIME TAKEN: {:.3f} s".format(time.time() - ts))

    return res

# ===


# === data procesing functions ===
# TOOD: test if this can go into a separate file(s)

@_benchmark
def get_s3_zarr_store():
    s3 = s3fs.S3FileSystem(
        anon=False,
        # TODO: remove on real lambda
        profile=AWS_PROFILE,
        client_kwargs=dict(
            region_name=AWS_REGION,
        )
    )
    # TODO: this ZARR_STORE should be specifiable via the API
    store = s3fs.S3Map(root=S3_ZARR_STORE, s3=s3, check=False)
    return store


@_benchmark
def rasterize(da):
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

    # TODO: remove - for testing only
    if True:
        tf.shade(qm).to_pil().save(os.path.join(_DATA_OUT, 'test_shader.png'))

    # ---
    # TODO: break out this part into a different function
    out_json = {
        'height': height,
        'width': width,
        'lat': qm.nav_lat.values.astype(np.float16).tolist(),
        'lon': qm.nav_lon.values.astype(np.float16).tolist(),
        'values': qm.values.ravel().astype(np.float16).tolist()
    }

    # TODO: in reality this will be stored in s3
    with open(os.path.join(_DATA_OUT, 'ovt_data.json'), 'w') as f:
        s = simplejson.dump(out_json, f, ignore_nan=True)

    # TODO: return s3 url instead
    return '/data/ovt_data/json'
    # ---


@_benchmark
def make_html_page(params, data_uri):
    # TODO: replace with appropriate s3 url
    js_include = '/js/main-svg.js'
    css_include = '/css/style.css'
    data_uri = '/data/ovt_data.json'

    index_template = jinja_env.get_template('index-template.html')

    return index_template.render(
        lat_range=params['lat_range'],
        lon_range=params['lon_range'],
        js_include=js_include,
        css_include=css_include,
        plot_data_url=data_uri
    )


@_benchmark
def extract_params(query_params):
    """
        Checks the query string and extracts the relevant parameters raises
        error if something cannot be parsed properly.

        Returns parsed params
    """
    # [ ] attempt to parse various fields raise error if cannot be parsed /
    # doesn't conform
    # [ ] TODO: change lat min/max to multi-value query
    # [ ] TODO: correct lat/lon to be in the right range
    dt = dateutil.parser.parse(query_params["time"])
    var = query_params["var"]
    valid_vars = ["temp"]
    if var not in valid_vars:
        raise KeyError("Invalid var: {}, only accept {}".format(var, valid_vars))

    lat_min = float(query_params.get("lat_min", -90))
    lat_max = float(query_params.get("lat_max", 90))
    lon_min = float(query_params.get("lon_min", -180))
    lon_max = float(query_params.get("lon_max", 180))

    MIN_LATLON = 5

    if np.abs(lat_max - lat_min) <= MIN_LATLON:
        lat_center = (lat_max + lat_min) / 2
        lat_min = lat_center - 2.5
        lat_max = lat_center + 2.5

    if np.abs(lon_max - lon_min) <= MIN_LATLON:
        lon_center = (lon_max + lon_min) / 2
        lon_min = lon_center - 2.5
        lon_max = lon_center + 2.5

    return {
        "lat_range": [lat_min, lat_max],
        "lon_range": [lon_min, lon_max],
        "var": var,
        "dt": dt
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
        t = construct_kdtree()
        
    # construct bounding box in terms of lat/lon
    # -- combining points to potentially improve query speed
    points = [ 
        [lat_range[0], lon_range[0]],
        [lat_range[1], lon_range[1]]
    ]

    # NOTES:
    # `query maps` (lat, lon) -> 1-D index for the kdtree
    # col_size required to convert 1-D indexing to 2-D
    # y_2 = rows, x_2 = col, col_size = len(x_2)

    col_size = ds.nav_lon.shape[1]
    dist, bbox_pt_1d = t.query(points)

    # construct bounding box in the x_2/y_2 space
    bbox_pt_2d = [
        (int(p / col_size), int(p % col_size))
        for p in bbox_pt_1d
    ]

    y_2_range = [bbox_pt_2d[0][0], bbox_pt_2d[1][0]]
    x_2_range = [bbox_pt_2d[0][1], bbox_pt_2d[1][1]]

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
                da[slice(*ys), slice(0, xs[0])],
                da[slice(*ys), slice(xs[1], None)]
            ],
            dim='x_2'
        )
    else:
        swapped = False
        da = da[slice(*ys), slice(*xs)]

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

if __name__ == '__main__':
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {
            "time": "2020-10-01",
            "var": "temp",
            "lat_min": -50,
            "lat_max": -20,
            "lon_min": 110,
            "lon_max": 140
        }
    }
    context = None
    lambda_handler(event, context)
