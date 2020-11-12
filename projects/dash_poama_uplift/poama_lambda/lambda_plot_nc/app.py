# === imports ===

# ===


# === setup logging ===

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
        var [required]: variable to plot

    Example:
        http://<path/to/lambda>/alpha/plot_nc??time=2020-01-05&var=temp&lat_range=50,75&lon_range=-50,50
    """
    # [ ] parse query strings
    # [ ] retrieve data from opendap
    # [ ] plot the data
    # [ ] log the various stages
    # [ ] if there is an error, raise the error and fail/respond fast

    return response

# ===


# === data procesing functions ===
# TOOD: test if this can go into a separate file

def extract_params(query_strings):
    """
        Checks the query string and extracts the relevant parameters raises
        error if something cannot be parsed properly.

        Returns parsed params
    """
    # [ ] attempt to parse various fields raise error if cannot be parsed /
    # doesn't conform

    return parsed_params


def load_opendap_dataset(params):
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
    # [ ] return json format with error message
    return response

# ===


# === helpers ===

def _benchmark(f)
    """
        Decorator to benchmark the various data processing functions
    """
    # [ ] add time profile/logging
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        f(args), kwargs)
    return wrapper

# ===
