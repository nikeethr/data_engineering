# === imports ===
import time
import dateutil.parser
import functools
import json
import logging
import xarray as xr
import numpy as np
from scipy.spatial import KDTree
# ===


LOCAL_MODE = False
AWS_REGION = 'ap-southeast-2'
S3_ZARR_STORE = 'fvt-test-zarr-nr/test_zarr_store.zarr'

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
    # [ ] parse query strings
    # [ ] retrieve data from opendap
    # [ ] plot the data
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
    with xr.open_zarr(store, consolidated=True) as ds:
        # if the entire dataset lies within the lat/lon ranges then don't do
        # any kdtree computations.
        if ds_within_lat_lon(params):
            # TODO
            pass
        else:
            kdtree = construct_kdtree(ds)

            # get x_2 y_2 range from lat lon range
            LOGGER.debug("lon: {}, lat: {}".format(
                [np.min(ds.nav_lon.values), np.max(ds.nav_lon.values)],
                [np.min(ds.nav_lat.values), np.max(ds.nav_lat.values)]
            ))
            x2_range, y2_range = get_x_2_y_2_from_lat_lon(
                ds, params['lon_range'], params['lat_range'])
            LOGGER.debug("{}, {}".format(x2_range, y2_range))

            da = slice_dataset()

    LOGGER.info(">>>> TOTAL TIME TAKEN: {:.3f} s".format(time.time() - ts))

    return None

# ===


# === data procesing functions ===
# TOOD: test if this can go into a separate file(s)

@_benchmark
def get_s3_zarr_store():
    s3 = s3fs.S3FileSystem(
        anon=False,
        # profile=AWS_PROFILE,
        client_kwargs=dict(
            region_name=AWS_REGION,
        )
    )
    # TODO: this ZARR_STORE should be specifiable via the API
    store = s3fs.S3Map(root=S3_ZARR_STORE, s3=s3, check=False)
    return store


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
        lat_1d = np.ravel(ds.nav_lat)
        lon_1d = np.ravel(ds.nav_lon)
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

    y_2_range = [bbox_pt_2d[0][0], bbox_pt_2d[0][1]]
    x_2_range = [bbox_pt_2d[1][0], bbox_pt_2d[1][1]]

    return x_2_range, y_2_range


@_benchmark
def get_slice_where(da, lon_range, lat_range):
    da_sliced = da.where(
        ((da.nav_lon >= lon_range[0]) &
        (da.nav_lon <= lon_range[1]) &
        (da.nav_lat >= lat_range[0]) &
        (da.nav_lat <= lat_range[1])),
        drop=True
    )
    return da_sliced

@_benchmark
def slice_dataset(ds, xs, ys, lons):
    # TODO: have a specific slicing for tripolar
    n_y, n_x = ds.shape

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

    
    LON_SPAN = 360 # degrees
    x_diff = xs[1] - xs[0]
    lon_diff = lon[1] - lon[0]



def load_opendap_dataset(params):
    """
        Returns the sliced data set according to params
    """
    # [ ] slice params
    # [ ] raise error if dataset doesn't conform

    return da


def load_zarr_s3_dataset(params):
    """
        Returns the sliced data set according to params
    """
    # [ ] slice params
    # [ ] raise error if dataset doesn't conform

    return da


def preprocess_plot_data(da):
    """
        Transforms the data to plot ready data. The main thing is that the
        lat/lon grids are not monotonically increasing/decreasing which is
        required for meshgrid plots.
    """
    # [ ] rearrange data so it's monotonically increasing
    # [ ] return data to be plotted
    return plot_data


def plot(plot_data):
    """
        Do the actual plot.
    """
    # [ ] meshgrid plot
    # [ ] layouts etc.
    # [ ] save plot in byte array
    # [ ] encode to base64
    return byte_array


def convert_plot_to_response(img_64, content_type):
    """
        Converts plot data to appropriate format based on header
    """
    # [ ] convert data to html or base64 depending on request header
    # [ ] build response
    return response


def embed_plot_in_html(img_64):
    """
        embeds plot in html document for display on browsers
    """
    # [ ] convert base64 byte array to html doc format (utf-8)
    return html


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



