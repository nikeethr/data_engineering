import dash
import dateutil.parser
from dateutil.relativedelta import relativedelta
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash.exceptions import PreventUpdate

from stf_app import data_fetch
from stf_app import figures as fg
from stf_app.app import app


@app.callback(
    [
        Output('graph-streamflow', 'figure'),
        Output('select-awrc-id', 'value')
    ],
    [Input('store-controls', 'modified_timestamp')],
    [
        State('store-controls', 'data'),
    ]
)
def update_fc_graph(store_ts, store_data):
    if not store_ts or not store_data:
        raise PreventUpdate

    fc_date = data_fetch.parse_fc_dt_utc(store_data['fc_date'])
    daily = store_data['daily']

    df_fc = data_fetch.get_fc_dataframe(
        fc_date,
        store_data['awrc_id'],
        daily=daily
    )

    # get past 4 days of observed data
    df_obs = data_fetch.get_obs_dataframe(
        fc_date - relativedelta(days=4),
        fc_date,
        store_data['awrc_id'],
        daily=daily
    )

    if daily:
        fig = fg.streamflow_daily(df_obs, df_fc)
    else:
        fig = fg.streamflow_hourly(df_obs, df_fc)

    return fig, store_data['awrc_id']


@app.callback(
    [
        Output('analysis-controls', 'className'),
        Output('forecast-controls', 'className')
    ],
    [Input('store-controls', 'modified_timestamp')],
    [State('store-controls', 'data')]
)
def switch_plot_controls(store_ts, store_data):
    if not store_ts or not store_data:
        raise PreventUpdate

    plot_type = store_data.get('plot_type', 'fc')
    if plot_type == 'fc':
        return ('hide-control', 'forecast-controls')
    elif plot_type == 'an':
        return ('analysis-controls', 'hide-control')
    else:
        raise PreventUpdate


@app.callback(
    Output('stf-map', 'figure'),
    [
        Input('stf-map', 'clickData'),
        Input('store-controls', 'modified_timestamp')
    ],
    [
        State('stf-map', 'figure'),
        State('store-controls', 'data')
    ]
)
def update_stf_map(click_data, ts, figure_data, store_data):
    ctx = dash.callback_context
    # initialisation
    init = not ctx.triggered
    if ctx.triggered:
        elem_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if init or (elem_id == 'stf-map' and click_data and figure_data):
        catchment = click_data['points'][0].get('location', None)
        if not catchment:
            raise PreventUpdate
        fig = fg.update_stf_map(figure_data, catchment)
        return fig

    if elem_id == 'store-controls' and ts and figure_data and store_data:
        fig = fg.update_stf_map_current_station(
            figure_data, store_data['awrc_id'])
        return fig

    # No appropriate data found
    raise PreventUpdate


@app.callback(
    Output('store-controls', 'data'),
    [
        Input('select-awrc-id', 'value'),
        Input('fc-date-picker', 'date'),
        Input('an-date-picker', 'date'),
        Input('slider-lead-days', 'value'),
        Input('slider-days-to-show', 'value'),
        Input('stf-map', 'clickData'),
        Input('toggle-freq', 'value'),
        Input('toggle-forecast-analysis', 'value'),
    ],
    [State('store-controls', 'data')]
)
def update_control_store(
        awrc_id, fc_date, an_start_date, lead_days, days_to_show, click_data,
        toggle_freq, toggle_fc_an, store_data):
    # TODO: change to update and use store as state
    # TODO: convert fc_date to timezone aware (as database can handle this)
    ctx = dash.callback_context
    # initialisation
    init = not ctx.triggered
    if ctx.triggered:
        elem_id = ctx.triggered[0]['prop_id'].split('.')[0]

    valid_ids =  [
        'select-awrc-id', 'fc-date-picker', 'toggle-freq',
        'toggle-forecast-analysis'
    ]
    if init or (elem_id in valid_ids and awrc_id and fc_date and an_start_date):
        store_data.update({
            'awrc_id': awrc_id,
            'fc_date': fc_date,
            'an_start_date': an_start_date,
            'an_days_to_show': days_to_show,
            'an_lead_days': lead_days,
            'daily': not toggle_freq,
            'plot_type': 'fc' if toggle_fc_an else 'an'
        })

        return store_data

    valid_ids = ['stf-map']
    if elem_id in valid_ids and click_data:
        custom_data = click_data['points'][0].get('customdata', {})
        awrc_id = custom_data.get('awrc_id', None)

        if not awrc_id:
            raise PreventUpdate
        store_data.update(**custom_data)

        return store_data

    # No appropriate data found
    raise PreventUpdate


# TODO:
"""
@app.callback(
    Output('fc-date-picker', 'value'),
    [Input('select-awrc_id', 'value')]
)
def update_fc_date_picker()
"""
