import os
import pandas as pd
import psycopg2
import re
import stf_conf

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIR, 'sample_data')
METADATA_CSV = os.path.join(DATA_DIR, 'metadata', 'station_metadata.csv')

# TODO: abstract out SRID
SRID_AUS=4283

# Only use following columns for now
# station_name, awrc_id, outlet_node, catchment, region, station_name

# UPSERT if already exists


def ingest():
    df_meta = pd.read_csv(METADATA_CSV)

    def to_sql_str(x):
        return "'" + re.sub(r"'", r"''", str(x)) + "'"

    def form_query_values(row):
        return "({})".format(
            ",".join([
                to_sql_str(row['awrc_id']),
                str(row['outlet_node']),
                to_sql_str(row['catchment']),
                to_sql_str(row['region']),
                to_sql_str(row['station_name']),
                "ST_SetSRID(ST_MakePoint({lon},{lat}),{srid})".format(
                    lon=row['lon'], lat=row['lat'], srid=SRID_AUS
                )
        ]))

    query_values = df_meta.apply(form_query_values, axis=1)
    query_values_str = ',\n'.join(query_values)
    print(query_values_str)

    # since this isn't huge data we can just INSERT instead of COPY, also
    # simpler to handle CONFLICTS this way.

    # TODO: do nothing for conlifct for now as UPDATE every column is a pain
    # esp since we may be adding more columns
    # This will need to change on the actual ingest code
    with psycopg2.connect(stf_conf.CONNECTION) as con:
        with con.cursor() as cur:
            query = """
                INSERT INTO stf_metadata (
                    awrc_id, outlet_node, catchment,region, station_name, location
                ) VALUES {} ON CONFLICT (awrc_id) DO NOTHING;
            """.format(query_values_str)
            # TODO: error handling?
            cur.execute(query)
            con.commit()


if __name__ == '__main__':
    ingest()
