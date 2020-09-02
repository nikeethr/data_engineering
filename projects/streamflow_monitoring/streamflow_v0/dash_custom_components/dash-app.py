import time
import json
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dash_custom_components import Calendar

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from flask_caching import Cache


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'THRESHOLD': 5
})

# TODO: investigate 'CACHE_THRESHOLD'

df_fc = pd.read_csv('../fc01.csv', index_col='time', parse_dates=True)
df_obs = pd.read_csv('../obs01.csv', index_col='time', parse_dates=True)


# mapbox_key = 'lipk.eyJ1IjoibmlrZWV0aHIiLCJhIjoiY2ptanY2YzZtMGVlZjNrbXFxZHY2Nm5qMCJ9.sG3MSE3-VfhZq36l_15xkw'

with open('../x.geojson') as f:
    geojson = json.load(f)

df_ovens_info = pd.read_csv('../ovens/VIC_station_model_idmap_ovens.csv')
df_ovens_info_json = df_ovens_info.to_json(indent=4)

def hex_to_rgb(h):
    h = h[1:]
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

hex_fc = '#902729'
hex_obs = '#09567E'
hex_grid_faint='#828282'

rgb_fc = hex_to_rgb(hex_fc)
str_rgba_fc = 'rgb{}'.format(rgb_fc + (1.0,))
str_rgba_fc_outer = 'rgba{}'.format(rgb_fc + (0.25,))
str_rgba_fc_inner = 'rgba{}'.format(rgb_fc + (0.4,))
str_rgba_transparent = 'rgba(0,0,0,0)'
str_rgba_grid_faint = 'rgba{}'.format(hex_to_rgb(hex_grid_faint) + (0.2,))

def random_data():
    YEARS_MAX = 5
    years = np.random.uniform(low=1, high=YEARS_MAX)
    start = pd.to_datetime('2014-01-01')
    end = start + relativedelta(years=int(years))

    date_range = pd.date_range(start, end)
    data = np.abs(np.random.normal(0, 1, size=len(date_range)))
    df = pd.DataFrame({'date': date_range, 'value': data})
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    return df.to_dict('records')


@cache.memoize(timeout=30)
def resample_hourly_to_daily(df):
    return df[:-1].resample('D', closed='left').sum()


# TODO: this callback should use the existing figure and update the layout...
def streamflow_daily():
    fig = go.Figure()

    df_fc_daily = resample_hourly_to_daily(df_fc)
    df_fc_daily = resample_hourly_to_daily(df_obs)

    df_fc_daily = df_fc[:-1].resample('D', closed='left').sum()
    df_obs_daily = df_obs[:-1].resample('D', closed='left').sum()

    # observation
    fig.add_trace(go.Scatter(
        x=df_obs_daily.index,
        y=df_obs_daily['obs'],
        marker_color=hex_obs,
	marker_size=12,
        name='observation'
    ))

    # for idx, row in df_obs_daily.iterrows():
    #     x0 = idx - pd.Timedelta(days=0.4)
    #     x1 = idx + pd.Timedelta(days=0.4)
    #     y0 = row['obs']
    #     y1 = row['obs']

    #     fig.add_shape(
    #         type='line', x0=x0, x1=x1, y0=y0, y1=y1,
    #         line={
    #             'color': hex_obs,
    #             'width': 6
    #         },
    #         name='observation'
    #     )

    # forecast
    fig.add_trace(go.Box(
        x=df_fc_daily.index,
        lowerfence=df_fc_daily['5'],
        q1=df_fc_daily['25'],
        median=df_fc_daily['50'],
        q3=df_fc_daily['75'],
        upperfence=df_fc_daily['95'],
        marker_color=hex_fc,
        name='forecast'
    ))

    # grid format
    fig.update_xaxes(gridcolor=str_rgba_grid_faint)
    fig.update_yaxes(gridcolor=str_rgba_grid_faint)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        margin={'l':0, 'r':0, 't':40, 'b':40},
        legend={'x':1, 'y':0.5}
    )

    return fig


def streamflow_hourly():
    fig = go.Figure()

    # plot observations
    fig.add_trace(
        go.Scatter(
            x=df_obs.index, y=df_obs['obs'], name='obs',
            line={
                'color': hex_obs,
                'width': 3
            }
        )
    )

    # plot streamflow
    sf_x = df_fc.index.to_series()
    sf_x_area = pd.concat([sf_x, sf_x.iloc[::-1]], ignore_index=True)

    fig.add_trace(go.Scatter(
        x = sf_x_area,
        y = pd.concat([df_fc['5'], df_fc['25'].iloc[::-1]], ignore_index=True),
        fill='toself',
        line_color=str_rgba_fc_outer,
        fillcolor=str_rgba_fc_outer,
        name='5-25 PCTL'
    ))

    fig.add_trace(go.Scatter(
        x = sf_x_area,
        y = pd.concat([df_fc['25'], df_fc['75'].iloc[::-1]], ignore_index=True),
        fill='toself',
        line_color=str_rgba_fc_inner,
        fillcolor=str_rgba_fc_inner,
        name='25-75 PCTL'
    ))

    fig.add_trace(go.Scatter(
        x = sf_x_area,
        y = pd.concat([df_fc['75'], df_fc['95'].iloc[::-1]], ignore_index=True),
        fill='toself',
        line_color=str_rgba_fc_outer,
        fillcolor=str_rgba_fc_outer,
        name='75-95 PCTL'
    ))

    fig.add_trace(
        go.Scatter(
            x=sf_x, y=df_fc['50'], name='median',
            line={
                'color': hex_fc,
                'width': 3
            }
        )
    )

    # grid format
    fig.update_xaxes(gridcolor=str_rgba_grid_faint)
    fig.update_yaxes(gridcolor=str_rgba_grid_faint)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        margin={'l':0, 'r':0, 't':40, 'b':40},
        legend={'x':1, 'y':0.5}
    )

    return fig


def plot_map():
    # data = go.Choroplethmapbox(
    #     locations=['ovens'],
    #     z=[1],
    #     geojson=geojson,
    #     featureidkey='properties.CATCHMENT',
    #     showscale=False
    # )

    data = go.Choropleth(
        locations=['ovens'],
        z=[1],
        geojson=geojson,
        featureidkey='properties.CATCHMENT',
        showscale=False
    )


    fig = go.Figure(data)

    # fig.update_layout(
    #     mapbox_zoom=3,
    #     mapbox_center={'lon': 133.77, 'lat': -25.27},
    #     mapbox_style='carto-positron',
    #     colorscale_sequential='viridis',
    #     margin={'l':0, 'r':0, 't':0, 'b':0},
    #     height=350,
    #     # mapbox_layers=[
    #     #     dict(
    #     #         source=geojson,
    #     #         type='fill',
    #     #         color='red',
    #     #         opacity=0.5,
    #     #         fill={'outlinecolor': '#FFF'},
    #     #         minzoom=5,
    #     #         name='ovens'
    #     #     )
    #     # ],
    # )

    fig.update_layout(
        colorscale_sequential='viridis',
        margin={'l':0, 'r':0, 't':0, 'b':0},
        height=350,
        geo={
            'showframe': False,
            'lonaxis': { 'range': [113.6594, 153.61194] },
            'lataxis': { 'range': [-43.00311, -12.46113] }
        }
    )



    """ for non-mapbox
        geo={
            'projection': {
                'type': 'mercator',
            },
            'lonaxis': { 'range': [113.6594, 153.61194] },
            'lataxis': { 'range': [-43.00311, -12.46113] }
        }
    """

    return dcc.Graph(id='map', figure=fig)

def form_tag(text):
    return html.Div(
        text,
        style={'color': 'steelblue', 'fontSize': 12, 'fontFamily': 'monospace'}
    )

modal = html.Div(
    [
        dbc.Button("Open Calendar", id="open"),
        dbc.Modal(
            [
                dbc.Button("Regenerate", id="calendar-button"),
                dbc.ModalHeader("Outlier Calendar"),
                dbc.ModalBody(html.Div(
                    Calendar(
                        id='calendar',
                        value='my-value',
                        label='my-label',
                        data=random_data()
                    ), style={'overflow-x': 'hidden', 'margin-top': 0, 'padding-top': 0})),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            scrollable=True,
            id="modal",
        ),
    ]
)

body = dbc.Container([
    dbc.Row(dbc.Col(
        html.H1('Streamflow'), md={'offset': 6, 'size': 3}
    )),

    dbc.Row(dbc.Col(
        html.Div('Dash: streamflow graph.'), md={'offset': 6, 'size': 3}
    )),


    dbc.Row([
        dbc.Col(dbc.Row(dbc.Col([
            plot_map(),
            html.Div([
                form_tag('FREQ'),
                dcc.Dropdown(
                    id='select-freq',
                    options = [
                        {'label': 'Daily', 'value': 'D'},
                        {'label': 'Hourly', 'value': 'H'}
                ])
            ]),
#             html.Div([
#                 form_tag('FORECAST DATE'),
# 		html.Div([
# 		    dcc.DatePickerSingle(
# 			id='my-date-picker-single',
# 			min_date_allowed=datetime(1995, 8, 5),
# 			max_date_allowed=datetime(2017, 9, 19),
# 			initial_visible_month=datetime(2017, 8, 5),
# 			date=str(datetime(2017, 8, 25, 23, 59, 59))
# 		    )
# 		], className='dash-bootstrap')
#             ]),

            html.Div([
                form_tag('OUTLIER CALENDAR'),
                modal
            ]),


            ])), md={'size': 6}),
            dbc.Col([
                html.Div(
                    dcc.Markdown('```\n' + df_ovens_info_json + '\n```'),
                )
            ], md= {'size': 6}, style={'overflow': 'auto', 'max-height': '350px'})
        ], style={'margin-top': '20px'}),

    dbc.Row(dbc.Col(
        dcc.Loading(
            id='loading-streamflow',
            children=[dcc.Graph(id='streamflow')],
            type='graph',
            style={ 'filter': 'sepia(.5)', 'width': '100%'}
        )
    ))
], className='mt-4')

app.layout = html.Div([body])

#TODO map click input should go into form that selects ovens as the location
@app.callback(
    Output('streamflow', 'figure'),
    [Input('select-freq', 'value'), Input('map', 'clickData')])
def update_streamflow(freq, mapdata):
    if freq =='H':
        return streamflow_hourly()
    else:
        return streamflow_daily()

@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(Output('calendar', 'data'), [Input('calendar-button', 'n_clicks'), Input('open', 'n_clicks')])
def display_output(n_clicks, n_clicks_2):
    d = random_data()
    return d

if __name__ == '__main__':
    app.run_server(debug=True)
