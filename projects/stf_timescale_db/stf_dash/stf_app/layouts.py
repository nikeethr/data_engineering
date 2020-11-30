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
                switch_controls()
            ], width=12, md=6),
        ]))
    ])


def select_awrc_id():
    awrc_ids = data_fetch.get_awrc_ids()
    options = [{ "label": x, "value": x } for x in awrc_ids ]

    return html.Div([
        dbc.Label('awrc id'),
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


def switch_controls():
    """
        switch between forecast and historical
    """
    return html.Div([
        html.Div([
            html.Div("ANALYSIS", id='label-analysis'),
            daq.ToggleSwitch(id='toggle-forecast-analysis', size=40, value=True),
            html.Div("FORECAST", id='label-forecast'),
        ], id='toggle-forecast-analysis-container'),
        html.Div([
            forecast_controls(hidden=False),
            analysis_controls(hidden=True)
        ], id="forecast-analysis-control")
    ], id="switch-analysis-forecast")


def forecast_controls(hidden=False):
    class_name = 'hide-control' if hidden else 'forecast-controls'

    fc_date_range = data_fetch.get_fc_date_range()
    start_date = data_fetch.strip_fc_date(fc_date_range[0])
    end_date = data_fetch.strip_fc_date(fc_date_range[1])

    return html.Div([
        dbc.Label('fc date (utc) | fc hour=23'),
        html.Div(dcc.DatePickerSingle(
            className="stf-date-picker",
            id="fc-date-picker",
            date=end_date,
            display_format='YYYY-MM-DD',
            min_date_allowed=start_date,
            max_date_allowed=end_date,
            show_outside_days=False
        ))
    ], id='forecast-controls', className=class_name)


def analysis_controls(hidden=True):
    MIN_LEAD_DAY = 1
    MAX_LEAD_DAY = 7
    MIN_DAYS_TO_SHOW = 5
    MAX_DAYS_TO_SHOW = 30
    DAY_STEP = 5

    class_name = 'hide-control' if hidden else 'analysis-controls'

    # change to obs date range?
    fc_date_range = data_fetch.get_fc_date_range()
    start_date = data_fetch.strip_fc_date(fc_date_range[0])
    end_date = data_fetch.strip_fc_date(fc_date_range[1])

    return html.Div([
        html.Div([
            dbc.Label('start date (utc)'),
            html.Div(dcc.DatePickerSingle(
                className="stf-date-picker",
                id="an-date-picker",
                date=start_date,
                display_format='YYYY-MM-DD',
                min_date_allowed=start_date,
                max_date_allowed=end_date,
                show_outside_days=False
            ))
        ]),
        html.Div([
            dbc.Label('lead day'),
            dcc.Slider(
                min=MIN_LEAD_DAY,
                max=MAX_LEAD_DAY,
                value=1,
                included=False,
                marks={ i: {'label': str(i)} for i in range(1, MAX_LEAD_DAY+1)},
                id='slider-lead-days'
            )
        ]),
        html.Div([
            dbc.Label('days to show'),
            dcc.Slider(
                min=MIN_DAYS_TO_SHOW,
                max=MAX_DAYS_TO_SHOW,
                value=20,
                included=True,
                step=DAY_STEP,
                marks={ i: {'label': str(i)} for i in range(5, MAX_DAYS_TO_SHOW+1, 5)},
                id='slider-days-to-show'
            )
        ])
    ], id='analysis-controls', className=class_name)
    

