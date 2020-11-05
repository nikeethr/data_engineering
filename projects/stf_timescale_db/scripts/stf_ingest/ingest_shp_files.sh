#!/bin/bash

set -e

SCRIPT_DIR=$(dirname $(readlink -f $0))
EXAMPLE_DIR=$SCRIPT_DIR/sample_data/shp_files
SAMPLE_CATCHMENT_SHP=$EXAMPLE_DIR/VIC_SWIFT_Subarea_ovens
SAMPLE_SUBAREA_SHP=$EXAMPLE_DIR/VIC_SWIFT_Subcatchment_ovens
DB_CFG=$SCRIPT_DIR/stf_tsdb.cfg

# --- read config file ---

declare -A DB_CONF

while IFS='=' read -r key value; do
    DB_CONF[$key]="${value}"
done < <(awk '
    /^\[(.*)\]$/ { 
        gsub(/[\[\]]/, "");
        x = $0;
    }
    /=/ {
        printf("%s.%s\n", x, $0);
    }
' $DB_CFG)

run_query() {
    PGPASSWORD=${DB_CONF[tsdb.passwd]} psql \
        -h ${DB_CONF[tsdb.hostname]} \
        -p ${DB_CONF[tsdb.port]} \
        -U ${DB_CONF[tsdb.user]} \
        -d ${DB_CONF[tsdb.dbname]} \
        -f $1
}


# --- ingest data ---

# demo catchments
# TODO: use stf_metadata to determine what catchments to load
STATE=VIC
CATCHMENTS=(
    "ovens"
    "uppermurray"
    "kiewa"
)
SRID=4238  # TODO: infer from file
TMP_SQL_CATCH="${SCRIPT_DIR}/.tmp_ctm_geom.sql"
TMP_SQL_SAREA="${SCRIPT_DIR}/.tmp_sba_geom.sql"
GEOM_TABLE_NAME_CATCH=stf_geom_subcatch
GEOM_TABLE_NAME_SAREA=stf_geom_subarea

# Test version: deleting tables before adding.
# TODO: modify to only append if doesn't exist (on conflict) - can shp2pgsql do this?
delete_tables=1
for c in "${CATCHMENTS[@]}"; do
    echo "--- $c ---"
    flag="-a"
    # first one => delete
    # -d drops the table before creating: for later on use -p then -a.
    if [ "$delete_tables" -eq "1" ]; then
        flag="-d"
        delete_tables=0
    fi

    echo "-- flag=$flag"

    # Subcatchment
    shp2pgsql ${flag} -s ${SRID} \
        -I "${EXAMPLE_DIR}/${c}/${STATE}_SWIFT_Subcatchment_${c}" \
        $GEOM_TABLE_NAME_CATCH > $TMP_SQL_CATCH
    run_query $TMP_SQL_CATCH

    # Subarea
    shp2pgsql ${flag} -s ${SRID} \
        -I "${EXAMPLE_DIR}/${c}/${STATE}_SWIFT_Subarea_${c}" \
        $GEOM_TABLE_NAME_SAREA > $TMP_SQL_SAREA
    run_query $TMP_SQL_SAREA
done


# --- OLD NOTES ---
# # Subcatchment
# # Test version: 
# # -d drops the table before creating: for later on use -p then -a.
# shp2pgsql -d -s 4238 -I "${SAMPLE_CATCHMENT_SHP}" stf_geom_subcatch > tmp_ctm_geom.sql
# run_query tmp_ctm_geom.sql

# # Subarea
# shp2pgsql -d -s 4238 -I "${SAMPLE_SUBAREA_SHP}" stf_geom_subarea > tmp_sba_geom.sql
# run_query tmp_sba_geom.sql

# NOTE: you can use ST_Union to combine the geometries to catchment level or
# use geopandas -> dissolve to do this in python

# Consider doing this since catchment level geoms are probably more likely to
# be used.
