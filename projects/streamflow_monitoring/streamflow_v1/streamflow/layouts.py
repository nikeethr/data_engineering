import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import datetime
from . import dummy_data as dd
from . import figures as fg


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
    catchments = dd.get_catchments()
    catchment_options = [
        {'label': x, 'value': x}
        for x in catchments
    ]
    return dbc.Card([
        dbc.CardHeader("Controls"),
        dbc.CardBody(dbc.Row([
            dbc.Col(html.Div([
                dbc.Label('Catchments'),
                dcc.Dropdown(
                    options=catchment_options,
                    multi=True,
                    id='catchment-dropdown'
                )
            ]), width=6, lg=12),
            dbc.Col(html.Div([
                dbc.Label('Date range'),
                dcc.DatePickerRange(id='date-picker')
            ]), width=6, lg=12)
        ]))
    ], id='app-nav')


# TODO should go into figures.py
def get_fig_matrix():
    x, y, z = dd.get_matrix_data()
    fig = go.Figure(data=go.Heatmap(
        x=x, y=y, z=z, xgap=2, ygap=2,
        colorbar=dict(
            title="<b>match score</b>",
            titleside="right",
            thickness=10
        ),
        colorscale="YlGnBu"
    ))
    fig.update_layout(
        xaxis_title="<b>forecast date</b>",
        yaxis_title="<b>lead time</b>",
        legend_title="forecast vs. observation match score",
        font=dict(
            size=12,
            color="Black"
        ),
        xaxis_showspikes=True,
        xaxis_spikemode="across",
        height=300,
        margin=dict(r=5,l=5,t=30,b=10),
#       # For highlights
        shapes= [dict(
            yref="paper",
            type="rect",
            x0=pd.to_datetime('2020-01-13'),
            y0='0',
            x1=pd.to_datetime('2020-01-14'),
            y1='1',
            fillcolor="rgba(255,255,255,0.5)",
            line_color="rgba(0,0,0,1)",
            line_width=2
        )]
    )
    return fig

# TODO should go into dummy_data? or persist_data?
def match_matrix_figure_store():
    fig = get_fig_matrix()
    return dcc.Store(
        id='matrix-figure-store',
        data=fig.to_dict()
    )


def layout_match_matrix():
    return dbc.Card([
        match_matrix_figure_store(),
        dbc.CardHeader('Daily Obs/Fcst Match Score'),
        dbc.CardBody(dcc.Graph(id='graph-matrix'))
    ])


def layout_toggle(daily=True):
    # Hidden div inside the app that stores the intermediate value
    return html.Div([
        html.Div("DAILY", id='label-daily'),
        daq.ToggleSwitch(id='toggle-freq', size=40),
        html.Div("HOURLY", id='label-hourly')
    ], id='toggle-freq-container')

def layout_streamflow_graph(daily=True):
    # hourly for now

    return dbc.Card([
        dbc.CardHeader('Streamflow Time-series'),
        dbc.CardBody([
            html.Div(
                dd.dump_streamflow_json_data(),
                id='intermediate-sf-value',
                style={'display': 'none'}
            ),
            layout_toggle(),
            dbc.Spinner(dcc.Graph(id='graph-streamflow'))
        ])
    ])

def layout_content():
    return dbc.Row([
        dbc.Col(
            layout_match_matrix(),
            width=12
        ),
        dbc.Col(
            layout_streamflow_graph(),
            width=12
        )
    ])
