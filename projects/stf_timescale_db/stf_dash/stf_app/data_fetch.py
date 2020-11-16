import os
import requests
import pandas as pd
import dash_core_components as dcc

DEBUG_STF_API_URI='http://localhost:8050/stf_api'
DEFAULT_AWRC_ID = '403227'
DT_FMT = '%Y-%m-%d %H:%M %Z'


# TODO: create intermediate store with datetime

def get_awrc_ids():
    # TODO: this can be cached with expiry timestamp
    uri = os.path.join(DEBUG_STF_API_URI, 'awrc_ids')
    r = requests.get(uri)
    if r.ok:
        return [x[0] for x in r.json()]


# TODO: make it timezone unaware as dash cannot handle this
def get_fc_date_range(awrc_id=DEFAULT_AWRC_ID):
    # TODO: this can be cached with expiry timestamp
    uri = os.path.join(DEBUG_STF_API_URI, 'fc_dates', awrc_id)
    r = requests.get(uri)
    if r.ok:
        d = r.json()
        return (d[0][0], d[0][1])


def get_obs_dataframe(start_dt, end_dt, awrc_id=DEFAULT_AWRC_ID):
    uri = os.path.join(DEBUG_STF_API_URI, 'obs', awrc_id,
        start_dt.strftime(DT_FMT), end_dt.strftime(DT_FMT))
    r = requests.get(uri)

    if r.ok:
        d = r.json()
        df = pd.DataFrame(data=d['entries'], columns=d['keys'])
        df = df.set_index('timestamp')
        df.index = pd.to_datetime(df.index)
        return df


def get_fc_dataframe(fc_dt, awrc_id=DEFAULT_AWRC_ID):
    uri = os.path.join(DEBUG_STF_API_URI, 'fc', awrc_id, fc_dt.strftime(DT_FMT))
    r = requests.get(uri)

    if r.ok:
        d = r.json()
        df = pd.DataFrame(data=d['entries'], columns=d['keys'])
        df = df.set_index('timestamp')
        df.index = pd.to_datetime(df.index)
        return df


def store_current_product():
    return dcc.Store(id='store-controls', data={})

