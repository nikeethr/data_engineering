import dateutil.parser
from flask import Blueprint
from flask import jsonify, make_response
from pytz import timezone
from sqlalchemy import func, and_, distinct
from sqlalchemy.dialects.postgresql import INTERVAL
from sqlalchemy.sql.functions import concat

from stf_api.models.test_models import (
    StfObsFlow, StfFcFlow, StfMetadatum, StfGeomSubarea, StfGeomSubcatch
)
from stf_api.models.base import db


stf_bp = Blueprint('stf_api', __name__, url_prefix='/stf_api')


@stf_bp.route('/fc/<awrc_id>/<fc_dt>')
def stf_fc_flow(awrc_id, fc_dt):
    """
        API:
        stf_api/fc/<awrc_id>/<fc_dt>

        IN:
            - awrc_id: AWRC ID of station (required)
            - fc_dt: forecast datetime (required)
        OUT (json):
            - pctl [5, 25, 50, 75, 90] for timestamped to each lead hour from
              forecast date

        ```sql
        SELECT (
            fc_datetime + (INTERVAL '1 hour') * lead_time_hours AS timestamp,
            pctl_5, pctl_25, pctl_50, pctl_75, pctl_95
        )
        FROM stf_fc_flow
        INNER JOIN stf_metadata ON stf_metadata.pk_meta = stf_fc_flow.meta_id
        WHERE stf_fc_flow.fc_datetime = <fc_dt_utc> AND stf_metadata.awrc_id = <awrc_id>
        ORDER BY timestamp ASC;
        ```
    """
    FORCE_FC_HOUR = 23
    dt_utc = parse_dt_to_utc(fc_dt)
    # force the forecast hour to 23:00
    dt_utc = dt_utc.replace(hour=FORCE_FC_HOUR)

    q = StfFcFlow.query.with_entities(
        (
            StfFcFlow.fc_datetime
            + StfFcFlow.lead_time_hours * func.cast(concat(1, ' HOURS'), INTERVAL)
        ).label('timestamp'),
        StfFcFlow.pctl_5,
        StfFcFlow.pctl_25,
        StfFcFlow.pctl_50,
        StfFcFlow.pctl_75,
        StfFcFlow.pctl_95
    ).join(
        StfMetadatum, StfMetadatum.pk_meta == StfFcFlow.meta_id
    ).filter(
        func.date_trunc('hour', StfFcFlow.fc_datetime) == func.date_trunc('hour', dt_utc),
        StfMetadatum.awrc_id == awrc_id
    ).order_by('timestamp')

    # TODO: send 404 if entry is empty...?
    return ts_response(q)


@stf_bp.route('/obs/<awrc_id>/<start_dt>/<end_dt>')
def stf_obs_flow(awrc_id, start_dt, end_dt):
    """
        API:
        stf_api/fc/<awrc_id>/<start_dt>/<end_dt>

        IN:
            - awrc_id: AWRC ID of station (required)
            - start_dt: starting observation datetime (required)
            - end_dt: ending observation datetime (required)
        OUT (json):
            - streamflow observation for each observation timestamp

        ```sql
        SELECT obs_datetime AS timestamp, value FROM stf_obs_flow
        INNER JOIN stf_metadata ON stf_metadata.pk_meta = stf_obs_flow.meta_id
        WHERE
            stf_metadata.awrc_id = <awrc_id> AND
            stf_metadata.obs_datetime >= <start_dt> AND
            stf_metadata.obs_datetime < <end_dt>
            
        ORDER BY timestamp ASC;
        ```
    """
    start_dt_utc = parse_dt_to_utc(start_dt)
    end_dt_utc = parse_dt_to_utc(end_dt)

    q = StfObsFlow.query.with_entities(
            StfObsFlow.obs_datetime.label('timestamp'),
            StfObsFlow.value
        ).join(
            StfMetadatum, StfMetadatum.pk_meta == StfObsFlow.meta_id
        ).filter(and_(
            StfMetadatum.awrc_id == awrc_id,
            StfObsFlow.obs_datetime >= start_dt_utc,
            StfObsFlow.obs_datetime < end_dt_utc
        )).order_by('timestamp')

    return ts_response(q)

@stf_bp.route('/geo/catchment_boundaries')
def stf_catchment_boundaries():
    """
        API:
        stf_api/geo/catchment_boundaries

        OUT (geojson):
            - feature collection of catchment boundaries

        The following is saved as a `view`: view_catchment_boundaries
        ```sql
        SELECT jsonb_build_object(
            'type',     'FeatureCollection',
            'features', jsonb_agg(features.feature)
        )
        FROM (
          SELECT jsonb_build_object(
            'type',       'Feature',
            'id',         gid,
            'geometry',   ST_AsGeoJSON(geom)::jsonb,
            'properties', to_jsonb(inputs) - 'gid' - 'geom'
          ) AS feature
          FROM (SELECT ST_Union(geom), catchment FROM stf_geom_subcatch) inputs
        ) features;
        ```
    """
    # TODO: convert view into a model in stf_api.models
    q = db.session.execute("""
        SELECT * FROM view_catchment_boundaries
    """)
    r = q.fetchall()

    # unpack entries and jsonify
    return jsonify(r[0][0])


def query_station_info(filt):
    q = StfMetadatum.query.with_entities(
        # gets all columns except location
        *[c for c in StfMetadatum.__table__.c if c.name != 'location']
    ).add_columns(
        func.ST_X(StfMetadatum.location).label('lon'),
        func.ST_Y(StfMetadatum.location).label('lat')
    ).filter(*filt)
    return q


@stf_bp.route('/meta/list_stations/<catchment>')
def stf_station_info_for_catchment(catchment, awrc_id=None):
    """
        API:
            stf_api/meta/station_info/<catchment>

        IN:
            - catchment: Name of the catchment to grab metedata

        OUT (json):
            - station information for all stations in the catchment including
              e.g. station location, awrc id

        SELECT
            *, ST_X(location) AS lon, ST_Y(location) AS lat
        FROM stf_metadata
        WHERE catchment = <catchment>
    """

    filt = [StfMetadatum.catchment == catchment]
    q = query_station_info(filt)
    return ts_response(q)


@stf_bp.route('/meta/list_station/<awrc_id>')
def stf_station_info_for_awrc_id(awrc_id):
    """
        same as `func:stf_station_info_for_catchment` but filter using AWRC_ID
        i.e. `WHERE awrc_id = <awrc_id>
    """
    filt = [StfMetadatum.awrc_id == awrc_id]
    q = query_station_info(filt)
    return ts_response(q)


# --- helper APIs ---

@stf_bp.route('/awrc_ids')
def stf_awrc_ids():
    """
        ```sql
        WITH unique_meta_id AS (
                SELECT distinct(meta_id) FROM stf_fc_flow
            )
        SELECT awrc_id FROM stf_metadata
        INNER JOIN unique meta_id ON stf_metadata.pk_meta = unique_meta_id.meta_id
        ```
    """
    t_unique_meta_id = StfFcFlow.query.with_entities(
        distinct(StfFcFlow.meta_id).label('meta_id')
    ).cte('unique_meta_id')

    q_awrc_ids = StfMetadatum.query.with_entities(
        StfMetadatum.awrc_id
    ).join(t_unique_meta_id, t_unique_meta_id.c.meta_id == StfMetadatum.pk_meta)

    return jsonify(q_awrc_ids.all())


# get forecast dates by awrc_id

@stf_bp.route('/fc_dates/<awrc_id>')
def stf_fc_dates(awrc_id):
    """
        ```sql
        WITH t_meta_id AS (
                SELECT pk_meta AS meta_id FROM stf_metadata
                WHERE awrc_id = <awrc_id>
            )
        SELECT MIN(fc_datetime), MAX(fc_datetime) FROM stf_metadata
        WHERE meta_id IN (SELECT pk_meta FROM t_meta_id)
        ```
    """
    t_meta_id = StfMetadatum.query.with_entities(
        StfMetadatum.pk_meta.label('meta_id')
    ).filter(StfMetadatum.awrc_id == awrc_id
    ).cte('t_meta_id')

    q_fc_dates = StfFcFlow.query.with_entities(
        func.min(StfFcFlow.fc_datetime).label('min_fc_date'),
        func.max(StfFcFlow.fc_datetime).label('max_fc_date')
    ).filter(StfFcFlow.meta_id.in_(t_meta_id))

    return jsonify(q_fc_dates.all())


# --- helper funcs ---

def parse_dt_to_utc(dt_str):
    dt = dateutil.parser.parse(dt_str)
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=timezone('utc'))
    else:
        dt_utc = dt.astimezone(timezone('utc'))
    return dt_utc


def ts_response(q):
    # TODO: enable this if using from browser
    # if 'Cache-Control' not in r.headers:
    #     r.headers['Cache-Control'] = 'public, max-age=86400, must-revalidate'
    return make_response(jsonify({
        'keys': [ x['name'] for x in q.column_descriptions ],
        'entries': q.all()
    }))

