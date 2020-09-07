import json
import dash
from dash.dependencies import (
    Input, Output, State, ALL, MATCH
)
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


def cb_nav_item(cat_config):
    inputs = []
    states = []

    def on_select_nav_item(n_clicks, classes):
        # see: https://dash.plotly.com/advanced-callbacks
        ctx = dash.callback_context

        if not ctx.triggered:
            return ["No product selected"], classes

        button_prop_id = ctx.triggered[0]['prop_id'].split('.')
        props = json.loads(button_prop_id[0])
        ctx.inputs[0][]
        import pdb; pdb.set_trace()
        return [props["key"]], classes

    app.callback(
        [ Output("selected-product-name", "children") ],
        [ Input({"type": "button-category-item", "key": ALL}, "n_clicks") ],
    )(on_select_nav_item)

# register callback functions to expand/collapse nav
# TODO: convert all of these to client-side
def register_server_side_callbacks():
    cat_config = nav_config.get_category_config()
    for product_group, categories in cat_config.items():
        for category, items in categories.items():
            elem_ids = nav_config.get_nav_group_elem_ids(
                product_group, category)
            cb_collapse(elem_ids)
    cb_nav_item(cat_config)

# TODO: possibly move to index.py??
register_server_side_callbacks()
