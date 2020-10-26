import dash_core_components as dcc
import dash_html_components as html

from . import nav_config

# TODO get from nav_config
DEFAULT_PRODUCT = 'anom'

def app_states():
    return [ store_current_product() ]

def store_current_product():
    prod_config = nav_config.get_products_config()
    return dcc.Store(
        id='store-current-product',
        data={ DEFAULT_PRODUCT: prod_config[DEFAULT_PRODUCT] }
    )
