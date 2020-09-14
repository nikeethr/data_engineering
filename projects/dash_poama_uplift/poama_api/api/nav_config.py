import os
import json
import pytz
import datetime
import dateutil.parser
from dateutil.relativedelta import relativedelta


# internal constants
_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.join(_DIR, 'configs')
_CATEGORIES_PATH = os.path.join(_CONFIG_DIR, 'categories.json')
_PRODUCTS_PATH = os.path.join(_CONFIG_DIR, 'products.json')
_CATEGORIES_CFG = None
_PRODUCTS_CFG = None

# product specific assumptions
_IMG_TYPE = 'png'
_CAST = 'rt'
_URL = r'http://poama.bom.gov.au/access-s1/bom'

# external constants
CONTROL_KEYS = ['variable', 'domain', 'forecast_period', 'value']
START_DATE = pytz.utc.localize(dateutil.parser.parse('20180601'))

# this is a local asset
PRODUCT_NOT_AVAILABLE = r'prod_not_avail.png'
TOOLTIP_NOT_AVAILABLE = r'no_product_info.png'


def get_products_config():
    if _PRODUCTS_CFG is None:
        with open(_PRODUCTS_PATH, 'r') as f:
            _PRODUCTS_CONFIG = json.load(f)
    return _PRODUCTS_CONFIG


def get_category_config():
    if _CATEGORIES_CFG is None:
        with open(_CATEGORIES_PATH, 'r') as f:
            _CATEGORIES_CONFIG = json.load(f)
    return _CATEGORIES_CONFIG


def get_image_path(
        product_id, variable, domain, forecast_period, value, fc_date):

    if not validate_date(fc_date):
        raise ValueError

    fc_dt = pytz.utc.localize(dateutil.parser.parse(fc_date))
    product_cfg = get_products_config()
    product_info = product_cfg[product_id]
    base_product = product_info['code'] if 'code' in product_info else product_id

    img_dir = r'/'.join([
        x for x in [base_product, variable, domain] if x != 'null'
    ])
    product_prefix = r'_'.join(
        x for x in [base_product, variable, domain, forecast_period, value]
        if x != 'null'
    )

    return r"{base_url}/plots/{img_dir}/{prefix}_{date}_{cast}.png".format(
        base_url=_URL,
        img_dir=img_dir,
        prefix=product_prefix,
        date=fc_dt.strftime('%Y%m%d'),
        cast=_CAST
    )


def get_tooltip_image_path(product_name, product_info):
    tooltip_path = "../common/img/example_" + product_name + ".png";

    if 'tooltip' in product_info:
        tooltip_path = product_info['tooltip']

    return r'{}/{}'.format(_URL, tooltip_path)


# TODO: this should probably go into a separate helper I'm lazy.
def get_max_date():
    MAX_DAYS_BEFORE_NOW = 3
    dt_now = datetime.datetime.now(datetime.timezone.utc)
    dt_max = dt_now - relativedelta(days=3)
    return dt_max


def validate_date(date_):
    try:
        dt = pytz.utc.localize(dateutil.parser.parse(date_))
        max_dt = get_max_date()
        return dt >= START_DATE and dt <= max_dt
    except (TypeError, ValueError) as e:
        return False
    return False
