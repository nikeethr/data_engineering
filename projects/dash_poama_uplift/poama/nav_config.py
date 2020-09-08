import os
import json


# internal constants
_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.join(_DIR, 'configs')
_CATEGORIES_PATH = os.path.join(_CONFIG_DIR, 'categories.json')
_PRODUCTS_PATH = os.path.join(_CONFIG_DIR, 'products.json')
_CATEGORIES_CFG = None
_PRODUCTS_CFG = None

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

