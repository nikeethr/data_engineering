import os
import json


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


def get_image_path(product_data, variable, domain, forecast_period, value):
    product_id = list(product_data.keys())[0]
    product_info = product_data[product_id]
    base_product = product_info['code'] if 'code' in product_info else product_id

    # TODO need to implement date
    DATE = '20200901'
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
        date=DATE,
        cast=_CAST
    )
