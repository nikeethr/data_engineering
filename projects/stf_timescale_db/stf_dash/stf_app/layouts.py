import datetime
import dash_bootstrap_components as dbc
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html

from stf_app import data_fetch
from stf_app import figures as fg


def layout_main():
    return html.Div([
        data_fetch.store_current_product(),
        dbc.Container(layout_content())
    ])


def layout_content():
    return dbc.Row([
        dbc.Col(
            layout_controls(),
            width=12
        ),
        dbc.Col(
            layout_streamflow_graph(),
            width=12
        )
    ])


def layout_map():
    return dcc.Graph(figure=fg.stf_map(), id='stf-map')


def layout_streamflow_graph():
    # hourly for now
    return dbc.Card([
        dbc.CardHeader('Streamflow Time-series'),
        dbc.CardBody([
            toggle_daily_or_hourly(),
            dbc.Spinner(dcc.Graph(id='graph-streamflow'))
        ])
    ])


def layout_controls():
    return dbc.Card([
        dbc.CardHeader('Controls'),
        dbc.CardBody(dbc.Row([
            dbc.Col(layout_map(), width=12, md=6),
            dbc.Col([
                select_awrc_id(),
                select_fc_date()
            ], width=12, md=6),
        ]))
    ])


def select_awrc_id():
    awrc_ids = data_fetch.get_awrc_ids()
    options = [{ "label": x, "value": x } for x in awrc_ids ]

    return html.Div([
        dbc.Label('awrc_id'),
        dbc.Select(
            id="select-awrc-id",
            options=options,
            value=options[0]["value"]
        )
    ])


def toggle_daily_or_hourly():
    return html.Div([
        html.Div("DAILY", id='label-daily'),
        daq.ToggleSwitch(id='toggle-freq', size=40, value=True),
        html.Div("HOURLY", id='label-hourly')
    ], id='toggle-freq-container')


def select_fc_date():
    fc_date_range = data_fetch.get_fc_date_range()
    start_date = data_fetch.strip_fc_date(fc_date_range[0])
    end_date = data_fetch.strip_fc_date(fc_date_range[1])

    return html.Div([
        dbc.Label('fc_date (utc) | fc_hour=23'),
        html.Div(dcc.DatePickerSingle(
            className="stf-date-picker",
            id="fc-date-picker",
            date=end_date,
            display_format='YYYY-MM-DD',
            min_date_allowed=start_date,
            max_date_allowed=end_date,
            show_outside_days=False
        ))
    ])


