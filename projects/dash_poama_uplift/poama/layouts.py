import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

from . import nav_config


def layout_main():
    return dbc.Container(
        dbc.Row([
            dbc.Col(layout_nav(), width=12, lg=3),
            dbc.Col(layout_content(), width=12, lg=9)
        ], no_gutters=False),
    )


def layout_nav():
    return html.Div([
        layout_nav_group_list(category)
        for category in nav_config.CATEGORIES
    ])


def layout_nav_group_list(category):
    elem_ids = nav_config.get_nav_group_elem_ids(category)
    return html.Div([
        dbc.Button('+ ' + category, id=elem_ids["button"], color="info"),
        dbc.Collapse(dbc.ListGroup([
            dbc.ListGroupItem("Item 1"),
            dbc.ListGroupItem("Item 2"),
            dbc.ListGroupItem("Item 3"),
        ]), id=elem_ids["collapse"])
    ], className="layout-nav-group-list")


def layout_content():
    return html.Div()
