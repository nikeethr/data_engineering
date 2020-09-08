import json
import dash
from dash.dependencies import (
    Input, Output, State, ALL, MATCH
)
from dash.exceptions import PreventUpdate

from .app import app
from . import nav_config


def cb_collapse(elem_ids):
    def toggle_collapse(n, old_is_open, category):
        is_open = old_is_open
        if n:   # if button has been clicked
            is_open = not old_is_open
        sign = '- ' if is_open else '+ '
        return (is_open, sign + str(category.lstrip('+- ')))

    app.callback(
        [
            Output(elem_ids["collapse"], "is_open"),
            Output(elem_ids["button"], "children")
        ],
        [ Input(elem_ids["button"], "n_clicks") ],
        [
            State(elem_ids["collapse"], "is_open"),
            State(elem_ids["button"], "children")
        ],
    )(toggle_collapse)


def cb_select_product(cat_config, prod_config):
    inputs = []
    states = []

    def on_select_nav_item(n_clicks):
        # see: https://dash.plotly.com/advanced-callbacks
        # The clientside version of callback_context also works:
        #   - dash_clientside.callback_context.triggered
        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate

        button_prop_id = ctx.triggered[0]['prop_id'].split('.')
        props = json.loads(button_prop_id[0])
        prod_id = props["key"]
        return { prod_id: prod_config[prod_id] }

    app.callback(
        Output("store-current-product", "data"),
        [ Input({"type": "button-category-item", "key": ALL}, "n_clicks") ],
    )(on_select_nav_item)

def cb_update_controls():
    def on_change_current_product(ts, data):
        if not ts or not data:
            raise PreventUpdate

        product_name = list(data.keys())[0]
        product_info = list(data.values())[0]
        options = []
        value = []
        disabled = []

        for control in nav_config.CONTROL_KEYS:
            options.append([
                { 'label': x, 'value': x }
                for x in product_info[control]
            ])
            value.append(product_info[control][0])
            disabled.append(product_info[control][0] == "null")
        return product_name, *options, *value, *disabled

    outputs_options = []
    outputs_value = []
    outputs_disabled = []

    for control in nav_config.CONTROL_KEYS:
        outputs_options.append(Output("select-{}".format(control), "options"))
        outputs_value.append(Output("select-{}".format(control), "value"))
        outputs_disabled.append(Output("select-{}".format(control), "disabled"))

    app.callback(
        [
            Output("selected-product-name", "children"),
            *outputs_options,
            *outputs_value,
            *outputs_disabled
        ],
        [ Input("store-current-product", "modified_timestamp") ],
        [ State("store-current-product", "data") ]
    )(on_change_current_product)


# register callback functions to expand/collapse nav
# TODO: convert all of these to client-side
def register_server_side_callbacks():
    cat_config = nav_config.get_category_config()
    prod_config = nav_config.get_products_config()

    for product_group, categories in cat_config.items():
        for category, items in categories.items():
            elem_ids = nav_config.get_nav_group_elem_ids(
                product_group, category)
            cb_collapse(elem_ids)

    cb_select_product(cat_config, prod_config)
    cb_update_controls()

# TODO: possibly move to index.py??
register_server_side_callbacks()
