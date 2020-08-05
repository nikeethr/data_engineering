import json
from dash.dependencies import Input, Output

from .app import app
from . import dummy_data as dd
from . import figures as fg


@app.callback(
    Output('streamflow-graph', 'figure'),
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
