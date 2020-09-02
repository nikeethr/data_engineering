import json
from dash.dependencies import Input, Output, ClientsideFunction

from .app import app
from . import dummy_data as dd
from . import figures as fg


@app.callback(
    Output('graph-streamflow', 'figure'),
    [Input('toggle-freq', 'value'), Input('intermediate-sf-value', 'children')]
)
def toggle_hourly(toggle_value, data):
    data = dd.load_streamflow_json_data(data)

    # left = daily
    # toggle left = false, toggle right = true
    is_daily = not toggle_value

    if is_daily:
        return fg.streamflow_daily(*data['daily'])

    return fg.streamflow_hourly(*data['hourly'])



# client_side callbacks
app.clientside_callback(
    ClientsideFunction('clientside', 'update_matrix_graph_layout'),
    Output(component_id='graph-matrix', component_property='figure'),
    [
        Input('matrix-figure-store', 'data'),
        Input('graph-matrix', 'clickData'),
        Input('slider-days', 'value')
    ]
)

app.clientside_callback(
    ClientsideFunction('clientside', 'update_station_dropdown'),
    Output(component_id='station-dropdown', component_property='options'),
    [
        Input('site-details-store', 'data'),
        Input('catchment-dropdown', 'value')
    ]
)
