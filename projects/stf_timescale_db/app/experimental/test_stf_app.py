import json
import time
import dateutil.parser
import functools
import cProfile
import io
import pstats
import contextlib
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import INTERVAL
from sqlalchemy.sql.functions import concat

from pytz import timezone

import stf_app
from stf_app.models.test_models import (
    StfObsFlow, StfFcFlow, StfMetadatum, StfGeomSubarea, StfGeomSubcatch
)

@contextlib.contextmanager
def profiled():
    """
        Usage:
        >>> with profiled():
        >>>     do_stuff()
    """
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('tottime') #cumulative
    ps.print_stats()
    # uncomment this to see who's calling what
    # ps.print_callers()
    print(s.getvalue())

app = stf_app.create_app()


# TODO: benchmark these tests
# TODO: move elsewhere
def test_db_operations():
    def print_all_columns(rows):
        for r in rows:
            d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
            print(d)

    SHOW_EXAMPLE = True

    with app.app_context():
        # == test getting fc data
        print("--- test: get_fc ---")

        start_time = time.time()

        with profiled():
            q = StfFcFlow.query.join(
                    StfMetadatum, StfMetadatum.pk_meta == StfFcFlow.meta_id
                ).filter(and_(
                    StfMetadatum.awrc_id == "403227",
                    StfFcFlow.fc_datetime == dateutil.parser.parse("2020-10-01 23:00Z")
                ))


            res = q.all()

        delta_t = time.time() - start_time

        if SHOW_EXAMPLE:
            print("Example:")
            print_all_columns(res[0:5])

        print("--- time taken (get_fc): {:.3f}s".format(delta_t))

        # == test getting obs data
        print("--- test: get_obs ---")

        start_time = time.time()

        with profiled():
            q = StfObsFlow.query.join(
                    StfMetadatum, StfMetadatum.pk_meta == StfObsFlow.meta_id
                ).filter(and_(
                    StfMetadatum.awrc_id == "403227",
                    StfObsFlow.obs_datetime < dateutil.parser.parse("2020-10-01 23:00Z")
                ))

            res = q.all()

        delta_t = time.time() - start_time

        if SHOW_EXAMPLE:
            print("Example:")
            print_all_columns(res[0:5])

        print("--- time taken (get_obs): {:.3f}s".format(delta_t))


        # == test geo stuff
        # -- sub catchment
        print("--- test: get_geom_subcatch ---")

        start_time = time.time()

        # TODO: create a view for this in postgresql
        q = StfGeomSubcatch.query.with_entities(
            StfGeomSubcatch.catchment,
            func.ST_AsGeoJSON(func.ST_Union(
                StfGeomSubcatch.geom
            )).label('catchment_poly')
        ).group_by(
            StfGeomSubcatch.catchment
        )

        res = q.all()

        delta_t = time.time() - start_time

        if SHOW_EXAMPLE:
            print("Example: {}".format(res[0]))

        print("--- time taken (get_geom_subcatch): {:.3f}s".format(delta_t))

        # -- sub area
        print("--- test: get_geom_subarea ---")

        start_time = time.time()

        # TODO: create a view for this in postgresql
        q = StfGeomSubarea.query.with_entities(
            func.ST_AsGeoJSON((StfGeomSubarea.geom)).label('subarea_poly')
        )

        res = q.all()

        delta_t = time.time() - start_time

        if SHOW_EXAMPLE:
            print("Example: {}".format(res[0]))

        print("--- time taken (get_geom_subarea): {:.3f}s".format(delta_t))

        # -- metadata
        print("--- test: get_metadata ---")

        start_time = time.time()

        q = StfMetadatum.query.filter(
            StfMetadatum.catchment.in_(["ovens", "kiewa", "uppermurray"])
        )

        res = q.all()

        delta_t = time.time() - start_time

        if SHOW_EXAMPLE:
            print("Example:")
            print_all_columns(res)

        print("--- time taken (get_metadata): {:.3f}s".format(delta_t))


def _benchmark(f):
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        print("--- test: {} ---".format(f.__name__))
        start_time = time.time()
        f(*args, **kwargs)
        res = delta_t = time.time() - start_time
        print("--- time taken ({}): {:.3f}s".format(f.__name__, delta_t))
        return res
    return _wrapper

@_benchmark
def test_fc_api(awrc_id, fc_dt):
    """
        API:
        stf_api/fc/{awrc_id}/{fc_dt_utc}

        IN:
            - awrc_id (required)
            - fc_date (required)
        OUT (json):
            - pctl [5, 25, 50, 75, 90] for timestamped to each lead hour from
              forecast date

        equivilent to:
        ```sql
            SELECT (
                fc_datetime + (INTERVAL '1 hour') * lead_time_hours AS timestamp,
                pctl_5, pctl_25, pctl_50, pctl_75, pctl_95
            )
            FROM stf_fc_flow
            JOIN stf_metadata
            WHERE stf_fc_flow.fc_datetime = <fc_dt_utc> AND stf_metadata.awrc_id = <awrc_id>
            ORDER BY timestamp ASC;
        ```
    """
    FORCE_FC_HOUR = 23
    dt = dateutil.parser.parse(fc_dt)
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=timezone('utc'))
    else:
        dt_utc = dt.astimezone(timezone('utc'))
    # forece the forecast hour to 23:00
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
    )

    return q.all()


def test_apis():
    AWRC_ID = '403227'
    META_ID = 193
    FC_DATETIME = '2020-10-01 23:00'

    with app.app_context():
        test_fc_api(AWRC_ID, FC_DATETIME)


if __name__ == '__main__':
    test_apis()
    # test_db_operations()
    # app.run(host='localhost', port=5000, debug=True)

