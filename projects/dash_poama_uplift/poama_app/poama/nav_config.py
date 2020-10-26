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
_URL_ACCESS_DEV = r'https://accessdev.nci.org.au/~gay548/reanal/'

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


def get_nav_group_elem_ids(product_group, category):
    cat_cfg = get_category_config()
    assert category in cat_cfg[product_group]
    return {
        'button': 'button-category-{}-{}'.format(product_group, category),
        'collapse': 'collapse-{}-{}'.format(product_group, category)
    }


def get_nav_item_id(product_group, category, item):
    cat_cfg = get_category_config()
    assert item in [list(x.keys())[0] for x in cat_cfg[product_group][category]]
    return 'group-item-{}-{}-{}'.format(product_group, category, item)


def get_image_path(product_data, variable, domain, forecast_period, value, date_):
    product_id = list(product_data.keys())[0]
    product_info = product_data[product_id]
    base_product = product_info['code'] if 'code' in product_info else product_id

    img_dir = r'/'.join([
        x for x in [base_product, variable, domain] if x != 'null'
    ])
    product_prefix = r'_'.join(
        x for x in [base_product, variable, domain, forecast_period, value]
        if x != 'null'
    )

    return r"{base_url}/{img_dir}/{prefix}_{date}_{cast}.png".format(
        base_url=_URL_ACCESS_DEV,
        img_dir=img_dir,
        prefix=product_prefix,
        date=date_.strftime('%Y%m%d'),
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
