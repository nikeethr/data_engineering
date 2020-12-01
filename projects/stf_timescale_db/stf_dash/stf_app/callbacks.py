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

    plot_type = store_data.get('plot_type', 'fc')

    if plot_type not in ['fc', 'an']:
        raise PreventUpdate

    daily = store_data['daily']

    agg = None
    if daily:
        agg = store_data.get('daily_agg_method', 'sum')

    if plot_type == 'fc':
        fc_date = data_fetch.parse_fc_dt_utc(store_data['fc_date'])
        df_fc = data_fetch.get_fc_dataframe(
            fc_date,
            store_data['awrc_id'],
            daily=daily,
            agg=agg
        )

        # get past 4 days of observed data
        df_obs = data_fetch.get_obs_dataframe(
            fc_date - relativedelta(days=4),
            fc_date,
            store_data['awrc_id'],
            daily=daily,
            agg=agg
        )
    else: # plot_type == 'an'
        days_to_show = store_data['an_days_to_show']
        lead_day = store_data['an_lead_day']

        obs_start_dt = data_fetch.parse_fc_dt_utc(store_data['an_start_date'])
        obs_end_dt = obs_start_dt + relativedelta(days=days_to_show)

        # subtract lead days so that start date is still included
        if daily:
            fc_start_dt = obs_start_dt - relativedelta(days=lead_day)
        else: # hourly
            # start 1 day less since e.g. day 1 includes hours 1 -> 24
            fc_start_dt = obs_start_dt - relativedelta(days=lead_day-1)
        fc_end_dt = fc_start_dt + relativedelta(days=days_to_show)

        df_fc = data_fetch.get_fc_lead_dataframe(
            fc_start_dt,
            fc_end_dt,
            lead_day,
            store_data['awrc_id'],
            daily=daily,
            agg=agg
        )

        # adding 1 hour shift so that it matches forecast range
        df_obs = data_fetch.get_obs_dataframe(
            obs_start_dt,
            obs_end_dt,
            store_data['awrc_id'],
            daily=daily,
            agg=agg
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
    Output('agg-controls', 'className'),
    [Input('store-controls', 'modified_timestamp')],
    [State('store-controls', 'data')]
)
def show_agg_if_daily(store_ts, store_data):
    if not store_ts or not store_data:
        raise PreventUpdate
    if store_data.get('daily', False):
        return 'agg-controls'
    else:
        return 'hide-control'


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
        Input('slider-lead-day', 'value'),
        Input('slider-days-to-show', 'value'),
        Input('stf-map', 'clickData'),
        Input('toggle-freq', 'value'),
        Input('toggle-forecast-analysis', 'value'),
        Input('select-agg-method', 'value'),
    ],
    [State('store-controls', 'data')]
)
def update_control_store(
        awrc_id, fc_date, an_start_date, lead_day, days_to_show, click_data,
        toggle_freq, toggle_fc_an, agg_method, store_data):
    # TODO: change to update and use store as state
    # TODO: convert fc_date to timezone aware (as database can handle this)
    ctx = dash.callback_context
    # initialisation
    init = not ctx.triggered
    if ctx.triggered:
        elem_id = ctx.triggered[0]['prop_id'].split('.')[0]

    valid_ids =  [
        'select-awrc-id', 'fc-date-picker', 'an-date-picker', 'toggle-freq',
        'toggle-forecast-analysis', 'slider-lead-day', 'slider-days-to-show',
        'select-agg-method'
    ]
    if init or (elem_id in valid_ids and awrc_id and fc_date and an_start_date):
        store_data.update({
            'awrc_id': awrc_id,
            'fc_date': fc_date,
            'an_start_date': an_start_date,
            'an_days_to_show': days_to_show,
            'an_lead_day': lead_day,
            'daily': not toggle_freq,
            'daily_agg_method': agg_method,
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
