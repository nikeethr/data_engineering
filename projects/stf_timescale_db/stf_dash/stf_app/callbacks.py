import dateutil.parser
from dateutil.relativedelta import relativedelta
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash.exceptions import PreventUpdate

from stf_app import data_fetch
from stf_app import figures as fg
from stf_app.app import app


@app.callback(
    Output('graph-streamflow', 'figure'),
    [Input('store-controls', 'modified_timestamp')],
    [State('store-controls', 'data')]
)
def update_fc_graph(store_ts, store_data):
    if not store_ts or not store_data:
        raise PreventUpdate

    fc_date = data_fetch.parse_fc_dt_utc(store_data['fc_date'])

    df_fc = data_fetch.get_fc_dataframe(
        fc_date,
        store_data['awrc_id']
    )

    # get past 4 days of observed data
    df_obs = data_fetch.get_obs_dataframe(
        fc_date - relativedelta(days=4),
        fc_date,
        store_data['awrc_id']
    )

    return fg.streamflow_hourly(df_obs, df_fc)


@app.callback(
    Output('stf-map', 'figure'),
    [Input('stf-map', 'clickData')],
    [State('stf-map', 'figure')],
)
def display_click_data(click_data, figure_data):
    if not click_data or not figure_data:
        raise PreventUpdate

    geojson = figure_data['data'][0]['geojson']
    location = click_data['points'][0]['location']
    
    # find center for coordinate
    # TODO: use go.Figure() to do this...
    # TODO: show station points for selected catchment
    for feature in geojson['features']:
        if feature['id'] == location:
            center = feature['properties']['center']['coordinates']
            bbox = feature['properties']['bbox']['coordinates'][0]
            lon_min = min([x[0] for x in bbox]) - 0.01
            lat_min = min([x[1] for x in bbox]) - 0.01
            lon_max = max([x[0] for x in bbox]) + 0.01
            lat_max = max([x[1] for x in bbox]) + 0.01

            figure_data['layout'].update({
                'transition': {
                    'duration': 500,
                    'easing': 'cubic-in-out'
                }
            })

            if 'center' not in figure_data['layout']['geo']:
                figure_data['layout']['geo']['center'] = {}

            figure_data['layout']['geo']['center'] = {
                'lon': center[0],
                'lat': center[1]
            }

            if 'projection' not in figure_data['layout']['geo']:
                figure_data['layout']['geo']['projection'] = {}

            figure_data['layout']['geo']['projection'].update({
                'scale': 130
            })
            break

    # TODO: get station points for catchment
    return figure_data


@app.callback(
    Output('store-controls', 'data'),
    [Input('select-awrc-id', 'value'), Input('fc-date-picker', 'date')],
    [State('store-controls', 'data')]
)
def update_control_store(awrc_id, fc_date, store_data):
    # TODO: change to update and use store as state
    # TODO: convert fc_date to timezone aware (as database can handle this)
    store_data.update({
        'awrc_id': awrc_id,
        'fc_date': fc_date
    })
    return store_data

# TODO:
"""
@app.callback(
    Output('fc-date-picker', 'value'),
    [Input('select-awrc_id', 'value')]
)
def update_fc_date_picker()
"""
