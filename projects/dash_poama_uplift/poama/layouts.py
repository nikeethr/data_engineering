import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

def layout_main():
    return dbc.Container(
        dbc.Row([
            dbc.Col(
                layout_nav(),
                width=12,
                lg=3
            ),
            dbc.Col(
                layout_content(),
                width=12,
                lg=9
            )
        ], no_gutters=False),
    )


def layout_nav():
    return html.Div()

def layout_content():
    return html.Div()
