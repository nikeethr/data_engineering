import os
import time
import io
import json
import functools
import pytz
import dateutil.parser
import psycopg2
import logging
import numpy as np
import pandas as pd
import xarray as xr
import s3fs


# --- const ---

BUCKET_NAME = 'stf-prototype-sample-data'
STFDB_INSTANCE_IP = os.environ.get('STFDB_INSTANCE_IP', 'localhost')
STFDB_USER = os.environ.get('STFDB_USER', 'postgres')
STFDB_PASSWD = os.environ.get('STFDB_PASSWD', '1234')
STFDB_NAME = 'stf_db'
STFDB_PORT = '5432'
STFDB_CONNECTION = 'postgres://{user}:{passwd}@{hostname}:{port}/{dbname}'.format(
    user=STFDB_USER,
    passwd=STFDB_PASSWD,
    hostname=STFDB_INSTANCE_IP,
    port=STFDB_PORT,
    dbname=STFDB_NAME
)
FC_TABLE_NAME = 'stf_fc_flow'
OBS_TABLE_NAME = 'stf_obs_flow'
AWS_PROFILE = 'my-stf-admin'
AWS_REGION = 'ap-southeast-2'
LOGGER = logging.getLogger(__name__)

# --- func ---

def ingest_stf_nc_to_db():
    # SAMPLE_NETCDF_FILE = 'sample_data/netcdf/kiewa/SWIFT-Ensemble-Observed-Flow_kiewa_20201009_2300.nc'
    SAMPLE_NETCDF_FILE = 'sample_data/netcdf/kiewa/SWIFT-Ensemble-Forecast-Flow_kiewa_20201009_2300.nc'
    fs = s3fs.S3FileSystem(
        anon=False,
        client_kwargs={ 'region_name': AWS_REGION },
        profile=AWS_PROFILE
    )
    if os.path.splitext(SAMPLE_NETCDF_FILE)[1] != '.nc':
        LOGGER.error("Incorrect file format. required *.nc")
        return
    else:
        with fs.open(os.path.join('s3://'+BUCKET_NAME, SAMPLE_NETCDF_FILE), 'rb') as f:
            if 'Observed-Flow' in SAMPLE_NETCDF_FILE:
                ingest_obs(f, SAMPLE_NETCDF_FILE)
            elif 'Forecast-Flow' in SAMPLE_NETCDF_FILE:
                ingest_fc(f, SAMPLE_NETCDF_FILE)
            else:
                LOGGER.error("Invalid stf netcdf filename")
                return


def ingest_fc(f_obj, fn):
    # decode_times = False because "hours since time of forecast" is not
    # recognizable
    start_time = time.time()

    with xr.open_dataset(f_obj, decode_times=False) as ds:
        # q_fcast_ens - variable name for ensemble forecast flow
        da_fc = ds['q_fcast_ens']

        # station_id actually refers to the node_id. We will extract the actual
        # station_id = awrc_id from the metadata later.
        da_nodes = ds['station_id']

        # forecast_start_time / catchment
        fc_dt, catchment = get_filename_info(fn)
        LOGGER.info('processing FORECAST flow for: {} @ {}'.format(
            catchment, fc_dt))

        for s in da_nodes.station:
            node_id = da_nodes.sel(station=s).item()
            LOGGER.debug('processing outlet_node={}...'.format(node_id))

            da_sel = da_fc.sel(station=s)

            # compute quantiles
            LOGGER.debug('  computing quantiles...')
            df_ingest = quantiles(da_sel)

            # populate forecast hour
            df_ingest['fc_datetime'] = fc_dt

            LOGGER.debug('  getting meta_id from db...')
            # meta_id is the primary key for the metadata table containing
            # the appropriate station information (including awrc_id)
            meta_id = get_station_pk(node_id, catchment)
            if meta_id is None:
                continue
            df_ingest['meta_id'] = meta_id
            LOGGER.debug('  meta_id={}'.format(meta_id))

            LOGGER.debug('  preparing dataframe...')
            # drop/rename/order columns to match database
            df_ingest.drop(columns='time', inplace=True)
            df_ingest.rename(
                columns={'lead_time': 'lead_time_hours'}, inplace=True)

            LOGGER.debug('  ingesting to timescaledb...')
            ingest_fc_to_db(df_ingest)

    delta_t = time.time() - start_time
    LOGGER.debug('Time taken - FORECAST flow - {} @ {}: {:.2f}s'.format(
        catchment, fc_dt, delta_t))


def ingest_obs(f_obj, fn):
    """
        similar to ingest_fc but has different variable mapping and subtleties
        so didn't combine it into one function
    """
    start_time = time.time()

    # obs doesn't have reference to "hours since time of forecast" so we can
    # decode normally
    with xr.open_dataset(f_obj) as ds:
        # q_der - variable name for observed flow
        da_obs = ds['q_der']
        da_nodes = ds['station_id']
        fc_dt, catchment = get_filename_info(fn)
        LOGGER.info('processing OBSERVED flow for: {} @ {}'.format(
            catchment, fc_dt))

        for s in da_nodes.station:
            node_id = da_nodes.sel(station=s).item()
            LOGGER.debug('processing outlet_node={}...'.format(node_id))

            da_sel = da_obs.sel(station=s)
            # can convert directly dataframe since no preprocessing actually
            # required
            df_ingest = da_sel.to_dataframe().reset_index()

            LOGGER.debug('getting meta_id from db...')
            # meta_id is the primary key for the metadata table containing
            # the appropriate station information (including awrc_id)
            meta_id = get_station_pk(node_id, catchment)
            if meta_id is None:
                continue
            df_ingest['meta_id'] = meta_id

            LOGGER.debug('preparing dataframe...')
            # rename appropriate columns
            df_ingest.rename(columns={
                'time': 'obs_datetime', 'q_der': 'value' }, inplace=True)

            LOGGER.debug('ingesting to timescaledb...')
            ingest_obs_to_db(df_ingest)

    delta_t = time.time() - start_time
    LOGGER.debug('Time taken - OBSERVED flow - {} @ {}: {:.2f}s'.format(
        catchment, fc_dt, delta_t))


# TODO: Maybe combine this with COPY e.g. do INSERT instead so it's all in one
# connection/transaction
def get_station_pk(node_id, catchment):
    with psycopg2.connect(STFDB_CONNECTION) as con:
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
        LOGGER.warning("metadata not found for catchment:node={}:{}".format(
            catchment, node_id))
        return None
    else:
        LOGGER.error("multiple ids found for catchment:node={}:{}. ids={}".format(
            catchment, node_id, station_pk))
        return None
    return station_pk


def quantiles(da):
    """
        Hack: I couldn't find a nice way of setting the output names of the
        columns after doing the quantile aggregations.
        - in sql you can use e.g. `percentile_cont(0.25) AS pctl_25`

        This is effectively:
        ```sql
        SELECT (
           lead_time,
           percentile_cont(0.05) WITHIN GROUP (ORDER BY value) AS pctl_5,
           percentile_cont(0.50) WITHIN GROUP (ORDER BY value) AS pctl_25,
           percentile_cont(0.25) WITHIN GROUP (ORDER BY value) AS pctl_50,
           percentile_cont(0.75) WITHIN GROUP (ORDER BY value) AS pctl_75,
           percentile_cont(0.95) WITHIN GROUP (ORDER BY value) AS pctl_95
        ) FROM df
        GROUP_BY lead_time
        ```
    """

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


def ingest_obs_to_db(df):
    """
        obs_datetime | timestamp with time zone | not null |
        meta_id      | integer                  | not null |
        value        | double precision         |          |
    """
    # process dataframe into buffer
    s_buf = io.StringIO()

    # order matters
    df[['obs_datetime', 'meta_id', 'value']].to_csv(
        s_buf, index=False, na_rep='NULL')
    s_buf.seek(0)

    # copy buffer
    copy_to_db(s_buf, stf_type='obs_flow')


def ingest_fc_to_db(df):
    """
        fc_datetime     | timestamp with time zone | not null |
        lead_time_hours | integer                  | not null |
        meta_id         | integer                  | not null |
        pctl_5          | double precision         |          |
        pctl_25         | double precision         |          |
        pctl_50         | double precision         |          |
        pctl_75         | double precision         |          |
        pctl_95         | double precision         |          |
    """
    # process dataframe into buffer
    s_buf = io.StringIO()

    # order matters
    df[['fc_datetime', 'lead_time_hours', 'meta_id', 'pctl_5', 'pctl_25',
        'pctl_50', 'pctl_75', 'pctl_95'
    ]].to_csv(s_buf, index=False, na_rep='NULL')
    s_buf.seek(0)

    # copy buffer
    copy_to_db(s_buf, stf_type='fc_flow')


def copy_to_db(values_buffer, stf_type, ignore_duplicates=False):
    stf_table_map = {
        'fc_flow': {
            'table': FC_TABLE_NAME,
            'temp_table': FC_TABLE_NAME + '_temp',
            'conflict_col': ['meta_id', 'lead_time_hours', 'fc_datetime']
        },
        'obs_flow': {
            'table': OBS_TABLE_NAME,
            'temp_table': OBS_TABLE_NAME + '_temp',
            'conflict_col': ['meta_id', 'obs_datetime']
        }
    }
    assert stf_type in stf_table_map.keys()
    d = stf_table_map[stf_type]

    # transaction to copy data
    # TODO: error handling?
    with psycopg2.connect(STFDB_CONNECTION) as con:
        with con.cursor() as cur:
            if ignore_duplicates:
                cur.copy_expert(
                    """
                        COPY {} FROM STDIN
                        WITH CSV HEADER DELIMITER ',' NULL 'NULL'
                    """.format(d['table']), values_buffer
                )
                con.commit()
            else:
                # create temporary table (and delete on commit)
                cur.execute(
                    """
                        CREATE TEMP TABLE {} (LIKE {}) ON COMMIT DROP;
                    """.format(d['temp_table'], d['table'])
                )
                # copy dataframe into temporary table
                cur.copy_expert(
                    """
                        COPY {} FROM STDIN
                        WITH CSV HEADER DELIMITER ',' NULL 'NULL'
                    """.format(d['temp_table']), values_buffer)
                # insert into main table with unique time/meta_id
                conflict_col_str = ', '.join(d['conflict_col'])
                cur.execute(
                    """
                        INSERT INTO {}
                        SELECT * FROM {}
                        ON CONFLICT ({}) DO NOTHING;
                    """.format(d['table'], d['temp_table'], conflict_col_str)
                )
                con.commit()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s|%(levelname)s|%(module)s.%(funcName)s]: %(message)s"
    )
    ingest_stf_nc_to_db()
