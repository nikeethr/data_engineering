import json
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

def store_site_details():
    site_details = dd.get_site_details()
    return dcc.Store(id='site-details-store', data=site_details)

def layout_nav():
    def layout_nav_location():
        site_details = dd.get_site_details()
        catchments = site_details.keys()
        catchment_options = [ {'label': x, 'value': x} for x in catchments ]

        return html.Div([
            store_site_details(),
            html.Div([
                dbc.Label('Catchment'),
                dcc.Dropdown(options=catchment_options, id='catchment-dropdown')
            ]),
            html.Div([
                dbc.Label('Station'),
                dcc.Dropdown(id='station-dropdown')
            ])
        ])

    def layout_nav_date():
        MIN_DAYS = 15
        MAX_DAYS = 45
        MID_DAYS = 30

        return html.Div([
            html.Div([
               dbc.Label('Start date'),
               dcc.DatePickerSingle(id='date-picker')
            ]),
            html.Div([
                dbc.Label('Days to show'),
                dcc.Slider(
                    id='slider-days', min=MIN_DAYS, max=MAX_DAYS,
                    value=MID_DAYS, step=1,
                    marks={
                        MIN_DAYS: '15',
                        MID_DAYS: '30',
                        MAX_DAYS: '45'
                    },
                    tooltip={
                        'placement': 'bottom',
                        'always_visible': False
                    })
            ]),
        ])

    return dbc.Card([
        dbc.CardHeader("Controls"),
        dbc.CardBody(dbc.Row([
            dbc.Col(layout_nav_location(), width=6, lg=12),
            dbc.Col(layout_nav_date(), width=6, lg=12)
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
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_showspikes=True,
        xaxis_spikemode="across",
        xaxis_fixedrange=True,
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        yaxis_fixedrange=True,
        height=300,
        margin=dict(r=5,l=5,t=30,b=10),
#       # For highlights
        shapes= [dict(
            yref="paper",
            type="rect",
            x0=pd.to_datetime('2020-01-13T12:00'),
            y0='0',
            x1=pd.to_datetime('2020-01-14T12:00'),
            y1='1',
            fillcolor="rgba(255,255,255, 0.3)",
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
