import time
import pandas as pd
import plotly.graph_objects as go
import time

from stf_app import data_fetch


SF_HEIGHT_PX = 400

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


def streamflow_daily(df_obs, df_fc):
    fig = go.Figure()

    # observation
    fig.add_trace(go.Scatter(
        x=df_obs.index,
        y=df_obs['value'],
        marker_color=hex_obs,
	marker_size=12,
        name='observation'
    ))

    # forecast
    fig.add_trace(go.Box(
        x=df_fc.index,
        lowerfence=df_fc['pctl_5'],
        q1=df_fc['pctl_25'],
        median=df_fc['pctl_50'],
        q3=df_fc['pctl_75'],
        upperfence=df_fc['pctl_95'],
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
        height=SF_HEIGHT_PX,
        # legend={'x':1, 'y':0.5},
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-.1,
            xanchor="right",
            x=1
        )
    )

    return fig


def streamflow_hourly(df_obs, df_fc):
    # NOTE: this function takes about 100ms - 150ms
    fig = go.Figure()

    # plot observations
    fig.add_trace(
        go.Scatter(
            x=df_obs.index, y=df_obs['value'], name='obs',
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
        y = pd.concat([df_fc['pctl_5'], df_fc['pctl_25'].iloc[::-1]],
                ignore_index=True),
        fill='toself',
        line_color=str_rgba_fc_outer,
        fillcolor=str_rgba_fc_outer,
        name='5-25 PCTL'
    ))

    fig.add_trace(go.Scatter(
        x = sf_x_area,
        y = pd.concat([df_fc['pctl_25'], df_fc['pctl_75'].iloc[::-1]],
                ignore_index=True),
        fill='toself',
        line_color=str_rgba_fc_inner,
        fillcolor=str_rgba_fc_inner,
        name='25-75 PCTL'
    ))

    fig.add_trace(go.Scatter(
        x = sf_x_area,
        y = pd.concat([df_fc['pctl_75'], df_fc['pctl_95'].iloc[::-1]],
                ignore_index=True),
        fill='toself',
        line_color=str_rgba_fc_outer,
        fillcolor=str_rgba_fc_outer,
        name='75-95 PCTL'
    ))

    fig.add_trace(
        go.Scatter(
            x=sf_x, y=df_fc['pctl_50'], name='median',
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
        height=SF_HEIGHT_PX,
        # legend={'x':1, 'y':0.5},
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-.1,
            xanchor="right",
            x=1
        )
    )

    return fig


def stf_map():
    geojson = data_fetch.get_catchment_boundaries()
    ids = [x['id'] for x in geojson['features']]
    colors = list(range(0, len(ids)))

    data = go.Choroplethmapbox(
        geojson=geojson,
        colorscale='geyser',
        marker_line_color='white', # line markers between states
        locations=ids,
        z=colors,
        showscale=False,
        marker_opacity=0.5,
        name='catchments'
    )

    fig = go.Figure(data=data)

    AUSTRALIA_CENTER_LON = 133.7751
    AUSTRALIA_CENTER_LAT = -25.2744
    AUSTRALIA_LON_RANGE = [113.338953078, 153.569469029]
    AUSTRALIA_LAT_RANGE = [-10.6681857235, -43.6345972634]

    fig.update_layout(
        autosize=True,
        margin=dict(t=0, b=0, l=0, r=0),
        height=300,
        mapbox_style="carto-positron",  # "carto-positron",  # open-street-map"
        mapbox=dict(
            center=dict(
                lat=AUSTRALIA_CENTER_LAT,
                lon=AUSTRALIA_CENTER_LON
            ),
            zoom=2
        ),
        showlegend=False
    )

    return fig


def update_stf_map_current_station(figure_data, awrc_id=None):
    # doing this is slow but allows for easier updating
    # TODO: adjust this to update directly instead
    fig = go.Figure(figure_data)

    df = data_fetch.get_station_info_for_awrc_id(awrc_id)

    curr_station_tr = go.Scattermapbox(
        lon=df['lon'],
        lat=df['lat'],
        mode='markers',
        marker_color='red',
        marker_size=12,
        name='curr_station',
         # TODO: nicer way of doing this...
        customdata=df[['awrc_id', 'station_name', 'catchment']].to_dict('records')
   )

    curr_station_tr_exist = False

    for x in figure_data['data']:
        if x['name'] == 'curr_station':
            curr_station_tr_exist = True

    if not curr_station_tr_exist:
        fig.add_trace(curr_station_tr)
    else:
        fig.update_traces(curr_station_tr, selector=dict(name='curr_station'))

    return fig


def update_stf_map(figure_data, catchment):
    # doing this is slow but allows for easier updating
    # TODO: adjust this to update directly instead
    fig = go.Figure(figure_data)
    
    # find center for coordinate
    # TODO: show station points for selected catchment
    geojson = figure_data['data'][0]['geojson']

    for feature in geojson['features']:
        if feature['id'] == catchment:
            center = feature['properties']['center']['coordinates']
            fig.update_layout(
                mapbox=dict(
                    center=dict(
                        lat=center[1],
                        lon=center[0]
                    ),
                    zoom=6
                )
            )

    df = data_fetch.get_station_info_for_catchment(catchment)

    tr_stations = go.Scattermapbox(
        lon=df['lon'],
        lat=df['lat'],
        mode='markers',
        marker_color='darkblue',
        marker_size=10,
        marker_opacity=0.6,
        name='stations',
        # TODO: nicer way of doing this...
        customdata=df[['awrc_id', 'station_name', 'catchment']].to_dict('records')
    )

    # TODO: there should be a better way of updating this.
    station_tr_exist = False
    for x in figure_data['data']:
        if x['name'] == 'stations':
            station_tr_exist = True

    if not station_tr_exist:
        fig.add_trace(tr_stations)
    else:
        fig.update_traces(tr_stations, selector=dict(name='stations'))

    return fig

    # TODO: get station points for catchment

