import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import numpy as np
import datetime


def layout_main():
    return dbc.Container(
        dbc.Row([
            dbc.Col(
                layout_nav(),
                width=12,
                md=3
            ),
            dbc.Col(
                layout_content(),
                width=12,
                md=9
            )
        ], no_gutters=False),
    )


def layout_nav():
    CATCHMENTS = [
        {'label': 'ovens', 'value': 'ovens'},
        {'label': 'uppermurray', 'value': 'uppermurray'},
        {'label': 'kiewa', 'value': 'kiewa'}
    ]
    return dbc.Card([
        dbc.CardHeader("NAVIGATION"),
        dbc.CardBody(dbc.Row([
            dbc.Col(html.Div([
                dbc.Label('Catchments'),
                dcc.Dropdown(
                    options=CATCHMENTS,
                    multi=True,
                    id='catchment-dropdown'
                )
            ]), width=6, md=12),
            dbc.Col(html.Div([
                dbc.Label('Date range'),
                dcc.DatePickerRange(id='date-picker')
            ]), width=6, md=12)
        ]))
    ], id='app-nav')

def get_figure():
    np.random.seed(1)

    programmers = ['Alex','Nicole','Sara','Etienne','Chelsea','Jody','Marianne']

    base = datetime.datetime.today()
    dates = base - np.arange(60) * datetime.timedelta(days=1)
    z = np.random.poisson(size=(len(programmers), len(dates)))

    fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=programmers,
            colorscale='Blues',
            showscale=False,
            xgap=2,
            ygap=2))

    fig.update_layout(
        xaxis_nticks=36,
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
        showlegend=False,
        margin=dict(r=0,l=0,t=0,b=0)
    )

    return dbc.Card([
        dbc.CardHeader('GitHub commits per day'),
        dbc.CardBody(dcc.Graph(figure=fig))
    ])

def layout_content():
    return get_figure()
