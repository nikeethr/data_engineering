import os
import json

_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_DIR = os.path.join(_DIR, 'configs')
_CATEGORIES_PATH = os.path.join(_CONFIG_DIR, 'categories.json')
_CATEGORIES_CFG = None


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
