import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import datetime

from . import nav_config
from . import states


# TODO: initialise layout with default product
def layout_main():
    return html.Div([
        states.store_current_product(),
        dbc.Container(
            dbc.Row([
                dbc.Col(layout_nav(), width=3),
                dbc.Col(layout_content(), width=9)
            ], no_gutters=False), fluid=True
        )
    ])


def layout_nav():
    cat_cfg = nav_config.get_category_config()
    return html.Div([
        layout_nav_info(),
        html.Div([
            dbc.Card([ 
                dbc.CardHeader(product_group, className="card-product-group-header"),
                dbc.CardBody([
                    layout_nav_group_list(product_group, category)
                    for category in categories
                ], className="card-product-group-body")
            ], color="primary", className="card-product-group")
            for product_group, categories in cat_cfg.items()
        ], id="layout-nav")
    ])



def layout_date():
    dt_max = nav_config.END_DATE

    return html.Div([
        dbc.Label('Forecast start date', id='forecast-start-date-label'),
        html.Div([
            dbc.Button('<', color='primary', id='button-prev-fc-date'),
            dcc.DatePickerSingle(
                min_date_allowed=nav_config.START_DATE,
                max_date_allowed=nav_config.END_DATE,
                display_format='YYYY-MM',
                date=str(dt_max.date()),
                id='forecast-start-date'
            ),
            dbc.Button('>', color='primary',
                id='button-next-fc-date', disabled=True)
        ])
    ])



def layout_tooltip():
    return html.Div([
        dbc.Button( "?", id="button-tooltip", color="primary"),
        dbc.Toast(
            html.Img(id='tooltip-image'),
            id="tooltip-toast",
            header="Product info",
            is_open=False,
            dismissable=True,
            icon="primary"
        ),
    ], id='container-toast')


def layout_nav_info():
    return dbc.Card([
        dbc.CardHeader("Info"),
        dbc.CardBody([
            html.Div([
                dbc.Badge("ACCESS-S1 FVT", color="info", pill=True, className="mr-1"),
                dbc.Badge("dev", color="success", pill=True, className="mr-1"),
                dbc.Badge("dash v1.x", color="danger",  pill=True,className="mr-1"),
            ]),
            layout_date()
        ], id="nav-info-body")
    ], color="primary", outline=True)


def layout_nav_group_list(product_group, category):
    cat_cfg = nav_config.get_category_config()
    elem_ids = nav_config.get_nav_group_elem_ids(product_group, category)
    return html.Div([
        dbc.Button('+ ' + category, id=elem_ids["button"], color="light"),
        # TODO
        # - inactive item (e.g. ['rt'] => forecast => show
        # is_active()
        dbc.Collapse(dbc.ListGroup([
            dbc.ListGroupItem(dbc.Button(
                list(item.keys())[0],
                color="Link",
                className='button-category-item',
                id={
                    'key': list(item.keys())[0], 'type': 'button-category-item'
                }
            ))
            for item in cat_cfg[product_group][category]
        ]), id=elem_ids["collapse"])
    ], className="layout-nav-group-list")


def layout_controls():
    # in order
    # | variable | domain | forecast_period | value |
    return dbc.Card([
        dbc.CardHeader("Controls"),
        dbc.CardBody(dbc.Row([
            dbc.Col([
                dbc.Label('variable'),
                dbc.Select(id='select-variable')
            ]),
            dbc.Col([
                dbc.Label('domain'),
                dbc.Select(id='select-domain')
            ]),
            dbc.Col([
                dbc.Label('forecast_period'),
                dbc.Select(id='select-forecast_period')
            ]),
            dbc.Col([
                dbc.Label('value'),
                dbc.Select(id='select-value')
            ]),
        ]))
    ], color='primary', outline=True)


def layout_product_img():
    return dbc.Card([
        dbc.CardHeader([
            html.Div(id="selected-product-name"),
            layout_tooltip()
        ]),
        dbc.CardBody([
            html.Div(id='product-path'),
            dbc.Spinner(html.Img(id='img-product'))
        ])
    ], color='primary', outline=True)


def layout_content():
    return html.Div([
        layout_controls(),
        layout_product_img()
    ])
