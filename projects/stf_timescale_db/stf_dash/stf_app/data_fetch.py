import time
import os
import requests
import pandas as pd
import dash_core_components as dcc
import dateutil
from dateutil.relativedelta import relativedelta
from pytz import timezone

DEBUG_STF_API_URI = 'http://localhost:8052/stf_api'
STF_API_URI = 'http://stf_api:8052/stf_api'
DEFAULT_AWRC_ID = '403227'
DT_FMT = '%Y-%m-%d %H:%M %Z'

# TODO: lot of duplication in some of these functions

# underlying assumption that all forecasts are at this hour (in UTC)
FORCE_FC_HOUR = 23


# TODO: create intermediate store with datetime

def get_awrc_ids():
    # TODO: this can be cached with expiry timestamp
    uri = os.path.join(STF_API_URI, 'awrc_ids')
    r = requests.get(uri)
    if r.ok:
        return [x[0] for x in r.json()]


# TODO: make it timezone unaware as dash cannot handle this
def get_fc_date_range(awrc_id=DEFAULT_AWRC_ID):
    # TODO: this can be cached with expiry timestamp
    uri = os.path.join(STF_API_URI, 'fc_dates', awrc_id)
    r = requests.get(uri)
    if r.ok:
        d = r.json()
        return (d[0][0], d[0][1])


def get_obs_dataframe(
        start_dt, end_dt, awrc_id=DEFAULT_AWRC_ID, daily=False, agg=None):
    # query range excludes end time - adding 1 hour to include it for hourly
    # for plot continuity.
    if not daily:
        end_dt += relativedelta(hours=1)
    uri = os.path.join(STF_API_URI, 'obs', awrc_id,
        start_dt.strftime(DT_FMT), end_dt.strftime(DT_FMT))
    payload = None

    if daily:
        agg = agg or 'sum'
        payload = { 'daily': True, 'daily_agg_method': agg }

    r = requests.get(uri, params=payload)

    if r.ok:
        d = r.json()
        df = pd.DataFrame(data=d['entries'], columns=d['keys'])
        df = df.set_index('timestamp')
        df.index = pd.to_datetime(df.index)
        return df


def get_fc_dataframe(fc_dt, awrc_id=DEFAULT_AWRC_ID, daily=False, agg=None):
    # fetch takes about 50ms
    uri = os.path.join(STF_API_URI, 'fc', awrc_id, fc_dt.strftime(DT_FMT))
    payload = None

    if daily:
        agg = agg or 'sum'
        payload = { 'daily': True, 'daily_agg_method': agg }

    r = requests.get(uri, params=payload)

    if r.ok:
        d = r.json()
        df = pd.DataFrame(data=d['entries'], columns=d['keys'])
        df = df.set_index('timestamp')
        # NOTE: to_datetime is slow, takes about 100ms
        df.index = pd.to_datetime(df.index)
        return df

def get_fc_lead_dataframe(
        start_date, end_date, lead_day, awrc_id=DEFAULT_AWRC_ID, daily=False,
        agg=None):
    """
        same as get_`fc_dataframe` but for a particular lead_day
    """
    uri = os.path.join(
        STF_API_URI, 'fc_lead', awrc_id, str(lead_day),
        start_date.strftime(DT_FMT), end_date.strftime(DT_FMT))
    payload = None

    if daily:
        agg = agg or 'sum'
        payload = { 'daily': True, 'daily_agg_method': agg }

    r = requests.get(uri, params=payload)

    if r.ok:
        d = r.json()
        df = pd.DataFrame(data=d['entries'], columns=d['keys'])
        df = df.set_index('timestamp')
        # NOTE: to_datetime is slow, takes about 100ms
        df.index = pd.to_datetime(df.index)
        return df

def get_catchment_boundaries():
    uri = os.path.join(STF_API_URI, 'geo', 'catchment_boundaries')
    r = requests.get(uri)
    if r.ok:
        return r.json()


def get_station_info_for_catchment(catchment):
    uri = os.path.join(
        STF_API_URI, 'meta', 'list_stations', catchment)
    r = requests.get(uri)
    if r.ok:
        d = r.json()
        df = pd.DataFrame(data=d['entries'], columns=d['keys'])
        return df


def get_station_info_for_awrc_id(awrc_id):
    uri = os.path.join(
        STF_API_URI, 'meta', 'list_station', awrc_id)
    r = requests.get(uri)
    if r.ok:
        d = r.json()
        df = pd.DataFrame(data=d['entries'], columns=d['keys'])
        return df


def store_current_product():
    return dcc.Store(id='store-controls', data={})


def parse_fc_dt_utc(dt_str, force_hour=True):
    dt = dateutil.parser.parse(dt_str)
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=timezone('utc'))
    else:
        dt_utc = dt.astimezone(timezone('utc'))
    if force_hour:
        dt_utc = dt_utc.replace(hour=FORCE_FC_HOUR)
    return dt_utc


def strip_fc_date(dt):
    # Usecase: Dash's single date picker will strip out the hour anyway but
    # will convert to local timezone.
    # plotly/dash is inconsistent with timezones so doing this to explicitly
    # keep it at UTC.

    # TODO: this truncation can probably happen @ postgres query and not
    # frontend.
    dt_utc = parse_fc_dt_utc(dt)
    return dt_utc.strftime('%Y-%m-%d')
