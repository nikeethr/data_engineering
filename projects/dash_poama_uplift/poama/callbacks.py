from dash.dependencies import (
    Input, Output, State
)
from .app import app
from . import nav_config


def toggle_collapse(n, old_is_open, category):
    is_open = old_is_open
    if n:   # if button has been clicked
        is_open = not old_is_open
    sign = '- ' if is_open else '+ '
    return (is_open, sign + str(category.lstrip('+- ')))


# register callback functions to expand/collapse nav
for category in nav_config.CATEGORIES:
    elem_ids = nav_config.get_nav_group_elem_ids(category)
    app.callback(
        [
            Output(elem_ids["collapse"], "is_open"),
            Output(elem_ids["button"], "children")
        ],
        [
            Input(elem_ids["button"], "n_clicks")
        ],
        [
            State(elem_ids["collapse"], "is_open"),
            State(elem_ids["button"], "children")
        ],
    )(toggle_collapse)
