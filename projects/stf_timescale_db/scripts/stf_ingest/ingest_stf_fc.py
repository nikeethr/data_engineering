import os
import io
import functools
import pytz
import dateutil.parser
import psycopg2
import numpy as np
import pandas as pd
import xarray as xr

# config
import stf_conf


# --- const ---

# stf data
DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIR, 'sample_data')
SAMPLE_FC_NC = os.path.join(
    DATA_DIR, 'ovens_example',
    'SWIFT-Ensemble-Forecast-Flow_ovens_20200929_2300.nc'
)
TABLE_NAME = 'stf_fc_flow'

# internal global vars
_DF_METADATA = None

# --- func ---


# TODO:
# - populate table

def ingest():
    # decode_times = False because "hours since time of forecast" is not
    # recognizable
    with xr.open_dataset(SAMPLE_FC_NC, decode_times=False) as ds:
        da_fc = ds['q_fcast_ens']
        # station_id actually refers to the node_id. We will extract the actual
        # station_id = awrc_id from the metadata later.
        da_nodes = ds['station_id']

        """
        for each node in file:
            - get station id
            - summarize ensemble members
            - create csv on lead time
            - ingest into database
        """
        # forecast_start_time / catchment
        fc_dt, catchment = get_filename_info(SAMPLE_FC_NC)

        for s in da_nodes.station:
            da_sel = da_fc.sel(station=s)

            # compute quantiles
            df_ingest = quantiles(da_sel)

            # get awrc_id
            node_id = da_nodes.sel(station=s).item()

            # populate forecast hour
            df_ingest['fc_datetime'] = fc_dt

            # meta identifier proxy for awrc_id
            meta_id = get_station_pk(node_id, catchment)
            if meta_id is None:
                continue
            df_ingest['meta_id'] = meta_id

            # drop/rename/order columns to match database
            df_ingest.drop(columns='time', inplace=True)
            df_ingest.rename(
                columns={'lead_time': 'lead_time_hours'}, inplace=True)

            ingest_df_to_db(df_ingest)


# TODO: Maybe combine this with COPY e.g. do INSERT instead so it's all in one
# connection/transaction
def get_station_pk(node_id, catchment):
    with psycopg2.connect(stf_conf.CONNECTION) as con:
        with con.cursor() as cur:
            query = """
                SELECT pk_meta FROM stf_metadata
                WHERE outlet_node = {} AND catchment = '{}'
            """.format(node_id, catchment)
            cur.execute(query)
            station_pk = cur.fetchall()
    if len(station_pk) == 1:
        station_pk = station_pk[0][0]
    elif len(station_pk) == 0:
        print("metadata not found for catchment:node={}:{}".format(
            catchment, node_id))
        return None
    else:
        print("multiple ids found for catchment:node={}:{}. ids={}".format(
            catchment, node_id, station_pk))
        return None
    return station_pk



def quantiles(da):
    # Hack: I couldn't find a nice way of setting the output names of the
    # columns after doing the quantile aggregations.
    # - in sql you can use e.g. `percentile_cont(0.25) AS pctl_25`
    # This is effectively:
    # ```
    # SELECT (
    #    lead_time,
    #    percentile_cont(0.05) WITHIN GROUP (ORDER BY value) AS pctl_5,
    #    percentile_cont(0.50) WITHIN GROUP (ORDER BY value) AS pctl_25,
    #    percentile_cont(0.25) WITHIN GROUP (ORDER BY value) AS pctl_50,
    #    percentile_cont(0.75) WITHIN GROUP (ORDER BY value) AS pctl_75,
    #    percentile_cont(0.95) WITHIN GROUP (ORDER BY value) AS pctl_95
    # ) FROM df
    # GROUP_BY lead_time

    q_dict = {
        'pctl_5': 0.05,
        'pctl_25': 0.25,
        'pctl_50': 0.50,
        'pctl_75': 0.75,
        'pctl_95': 0.95
    }
    qtl_funcs = []

    # create set of precentile agg functions
    for k in q_dict:
        f = functools.partial(np.quantile, q=q_dict[k])
        f.__name__ = k
        qtl_funcs.append(f)

    # perform agg over created functions
    # - drops ens_member as it is not required
    df = (da.to_dataframe()
            .reset_index()
            .drop(columns="ens_member")
            .groupby(["lead_time", "time"])
            .agg(qtl_funcs))

    # cleanup indices
    df.columns = df.columns.droplevel()
    df.reset_index(inplace=True)

    return df


def get_filename_info(fn):
    # TODO: redo this using regex to make it clearer
    fn_info = os.path.basename(fn).split('_')
    catchment = fn_info[1]
    fc_dt = dateutil.parser.parse('{} T{}'.format(
        fn_info[2], fn_info[3].split('.')[0]
    ))
    fc_dt = pytz.utc.localize(fc_dt)
    return fc_dt, catchment


def ingest_df_to_db(df):
    """
        fc_datetime     | timestamp with time zone |           | not null |
        lead_time_hours | integer                  |           | not null |
        meta_id         | integer                  |           | not null |
        pctl_5          | double precision         |           |          |
        pctl_25         | double precision         |           |          |
        pctl_50         | double precision         |           |          |
        pctl_75         | double precision         |           |          |
        pctl_95         | double precision         |           |          |
    """
    # process dataframe into buffer
    s_buf = io.StringIO()

    # order matters
    df[[
        'fc_datetime', 'lead_time_hours', 'meta_id', 'pctl_5', 'pctl_25',
        'pctl_50', 'pctl_75', 'pctl_95'
    ]].to_csv(s_buf, index=False, na_rep='NULL')
    s_buf.seek(0)

    # transaction to copy data
    with psycopg2.connect(stf_conf.CONNECTION) as con:
        with con.cursor() as cur:
            # TODO: error handling?
            # TODO: duplicate handling?
            cur.copy_expert(
                """
                    COPY {} FROM STDIN
                    WITH CSV HEADER DELIMITER ',' NULL 'NULL'
                """.format(TABLE_NAME), s_buf
            )
            con.commit()

# ---

# --- depreciated ---
# TODO:
# These are depreciated since getting meta info from postgres DB instead

def get_df_metadata():
    global _DF_METADATA
    if _DF_METADATA is None:
        _DF_METADATA = pd.read_csv(METADATA_CSV)
    return _DF_METADATA

def get_awrc_id(node_id, catchment, from_db=True):

    METADATA_CSV = os.path.join(DATA_DIR, 'ovens_example', 'station_metadata.csv')
    df_meta = get_df_metadata()

    awrc_id = df_meta.loc[
        (df_meta["catchment"] == "ovens") & 
        (df_meta["outlet_node"] == node_id)
    ]["awrc_id"]

    return awrc_id.item()

# ---

if __name__ == '__main__':
    ingest()
