import json
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta as rd

def get_site_details():
    SITE_DETAILS = {
        'ovens': [ '1111', '1112', '1113' ],
        'kiewa': [ '2111', '2112', '2113' ],
        'uppermurray': [ '3111', '3112', '3113' ]
    }
    return SITE_DETAILS

def get_matrix_data():
    ROWS = 7
    COLUMNS = 30

    # TODO this will eventually be an argument
    # and potentially will be year of month
    start_date = pd.to_datetime('2020-01-01')

    col_labels = pd.date_range(
        start_date, start_date + rd(days=COLUMNS-1))
    row_labels = [str(x) + 'd' for x in np.arange(1, ROWS+1, dtype=int)]
    data = np.random.random((7, 30))

    return (col_labels, row_labels, data)

def get_streamflow_data_hourly():
    N_ENS = 10
    LEAD_TIME_D = 7  # Days
    LEAD_TIME_H = LEAD_TIME_D * 24  # Hours
    QUANTILES = [5, 25, 50, 75, 95]

    start_date = pd.to_datetime('2020-01-01')
    end_date = start_date + rd(days=LEAD_TIME_D)
    time_idx = pd.date_range(start_date, end_date, freq='H')


    alpha = 2
    beta = 5

    fcst_ens = np.random.beta(alpha, beta, (LEAD_TIME_H, N_ENS))
    fcst_ens = np.percentile(fcst_ens, q=QUANTILES, axis=1)
    pd_fcst_ens = pd.DataFrame(fcst_ens.T, index=time_idx[:-1], columns=QUANTILES)

    obs = np.random.beta(alpha, beta, (LEAD_TIME_H, 1))
    pd_obs = pd.DataFrame(obs, index=time_idx[:-1], columns=['value'])

    return pd_obs, pd_fcst_ens


def dump_streamflow_json_data():
    data_hourly = get_streamflow_data_hourly()
    pd_obs, pd_fc = data_hourly
    convert_to_daily = lambda x: x[:-1].resample('D', closed='left').sum()
    data_daily = convert_to_daily(pd_obs), convert_to_daily(pd_fc)

    # convert to dict
    cvt_to_json = lambda dfs: [df.to_json() for df in dfs]
    data_daily, data_hourly = cvt_to_json(data_daily), cvt_to_json(data_hourly)

    return json.dumps({
        'daily': data_daily,
        'hourly': data_hourly
    })

def load_streamflow_json_data(s):
    d = json.loads(s)
    cvt_to_pandas = lambda ds: [pd.read_json(d) for d in ds]
    return {
        'daily': cvt_to_pandas(d['daily']),
        'hourly': cvt_to_pandas(d['hourly'])
    }


if __name__ == '__main__':
    # Test cases here
    # TODO move to better location

    print(get_catchments())
    print(get_matrix_data())

    d = dump_streamflow_json_data()
    print(d)
    d = load_streamflow_json_data(d)
    print(d)
