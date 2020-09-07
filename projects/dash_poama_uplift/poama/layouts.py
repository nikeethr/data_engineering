import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

from . import nav_config


def layout_main():
    return dbc.Container(
        dbc.Row([
            dbc.Col(layout_nav(), width=3),
            dbc.Col(layout_content(), width=9)
        ], no_gutters=False), fluid=False
    )


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


def layout_nav_info():
    return dbc.Card([
        dbc.CardHeader("Info"),
        dbc.CardBody([
            dbc.Badge("ACCESS-S1 FVT", color="info", pill=True, className="mr-1"),
            dbc.Badge("dev", color="success", pill=True, className="mr-1"),
            dbc.Badge("dash v1.x", color="danger",  pill=True,className="mr-1"),
            html.Div("Selected product", id="selected-product-name")
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


def layout_content():
    return html.Div()
