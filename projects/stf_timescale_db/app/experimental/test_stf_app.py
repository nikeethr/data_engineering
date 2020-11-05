import json
import time
import dateutil.parser
from sqlalchemy import func as sql_func

import stf_app
from stf_app.models.test_models import (
    StfObsFlow, StfMetadatum, StfGeomSubarea, StfGeomSubcatch, StfMetadatum
)

app = stf_app.create_app()


# TODO: benchmark these tests
# TODO: move elsewhere
def test_db_operations():
    with app.app_context():
        # == test getting obs data

        print("--- test: get_obs ---")

        start_time = time.time()

        res = StfObsFlow.query.join(
                StfMetadatum, StfMetadatum.pk_meta == StfObsFlow.meta_id
            ).filter(
                StfMetadatum.awrc_id == "403227",
                StfObsFlow.obs_datetime < dateutil.parser.parse("2020-10-01 23:00Z")
            )
        res.all()

        print("--- time taken (get_obs): {:.3f}s".format(time.time() - start_time))


        # == test getting fc data
        # TODO


        # == test geo stuff
        # -- sub catchment
        print("--- test: get_geom_subcatch ---")

        start_time = time.time()

        # TODO: create a view for this in postgresql
        res = StfGeomSubcatch.query.with_entities(
            StfGeomSubcatch.catchment,
            sql_func.ST_AsGeoJSON(sql_func.ST_Union(
                StfGeomSubcatch.geom
            )).label('catchment_poly')
        ).group_by(
            StfGeomSubcatch.catchment
        )
        res.all()

        print("--- time taken (get_geom_subcatch): {:.3f}s".format(time.time() - start_time))

        # -- sub area
        # TODO

        # -- metadata
        # TODO


if __name__ == '__main__':
    test_db_operations()
    # app.run(host='localhost', port=5000, debug=True)

