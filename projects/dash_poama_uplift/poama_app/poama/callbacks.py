import os
import base64
import json
import pytz
import dateutil.parser
import dash
import requests
from dash.dependencies import (
    Input, Output, State, ALL, MATCH
)
from dash.exceptions import PreventUpdate
from dateutil.relativedelta import relativedelta

from .app import app
from . import nav_config



@app.callback(
    Output("forecast-start-date", "date"),
    [
        Input("button-prev-fc-date", "n_clicks"),
        Input("button-next-fc-date", "n_clicks")
    ],
    State("forecast-start-date", "date")
)
def adjust_forecast_date(n_prev, n_next, date_):
    # see: https://dash.plotly.com/advanced-callbacks
    # The clientside version of callback_context also works:
    #   - dash_clientside.callback_context.triggered
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    try:
        dt = dateutil.parser.parse(date_)
        dt = pytz.utc.localize(dt)
    # TODO: specific exception
    except Exception as e:
        raise PreventUpdate

    button_prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if 'next' in button_prop_id:
        dt_new = dt + relativedelta(months=1)
        return str(dt_new.date())
    elif 'prev' in button_prop_id:
        dt_new = dt - relativedelta(months=1)
        return str(dt_new.date())
    else:
        raise PreventUpdate


@app.callback(
    [
        Output("button-prev-fc-date", "disabled"),
        Output("button-next-fc-date", "disabled")
    ],
    [ Input("forecast-start-date", "date") ]
)
def disable_forecast_adjustment(date_):
    try:
        dt = dateutil.parser.parse(date_)
        dt = pytz.utc.localize(dt)
    # TODO: specific exception
    except Exception:
        raise PreventUpdate

    dt_max = nav_config.END_DATE
    dt_min = nav_config.START_DATE

    if dt.date() <= dt_min.date():
        return [True, False]
    elif dt.date() >= dt_max.date():
        return [False, True]

    return [False, False]


@app.callback(
    Output("tooltip-toast", "is_open"),
    [Input("button-tooltip", "n_clicks")],
)
def open_toast(n):
    return True if n else False


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

        tooltip_path = nav_config.get_tooltip_image_path(product_name, product_info)
        r = requests.head(tooltip_path)

        if not r.ok:
            tooltip_path = app.get_asset_url(nav_config.TOOLTIP_NOT_AVAILABLE)

        return product_name, tooltip_path, *options, *value, *disabled

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
            Output("tooltip-image", "src"),
            *outputs_options,
            *outputs_value,
            *outputs_disabled
        ],
        [ Input("store-current-product", "modified_timestamp") ],
        [ State("store-current-product", "data") ]
    )(on_change_current_product)


def cb_update_product_image():
    def on_control_change(variable, domain, forecast_period, value, date_, ts, data):
        if not ts or not data:
            raise PreventUpdate

        try:
            dt = dateutil.parser.parse(date_)
            dt = pytz.utc.localize(dt)
        # TODO: specific exception
        except Exception:
            raise PreventUpdate

        image_path = nav_config.get_image_path(
            data, variable, domain, forecast_period, value, dt)
        # TODO: move somewhere else
        AUTH = (os.environ['ACCESS_DEV_USER'], os.environ['ACCESS_DEV_PASSWD'])

        r = requests.get(
            image_path, auth=AUTH, allow_redirects=True, stream=True
        )

        if not r.ok:
            return [
                app.get_asset_url(nav_config.PRODUCT_NOT_AVAILABLE),
                image_path
            ]

        img = r.raw.read()

        return [
            'data:image/png;base64,{}'.format(
                base64.b64encode(img).decode('utf-8')),
            image_path
        ]

    inputs_value = [
        Input("select-{}".format(control), "value")
        for control in nav_config.CONTROL_KEYS
    ]

    app.callback(
        [  
            Output('img-product', 'src'),
            Output('product-path', 'children')
        ],
        [
            *inputs_value,
            Input("forecast-start-date", "date"),
            Input("store-current-product", "modified_timestamp")
        ],
        [ State("store-current-product", "data") ]
    )(on_control_change)


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
    cb_update_product_image()

# TODO: possibly move to index.py??
register_server_side_callbacks()
