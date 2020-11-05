#!/bin/bash

TABLES=(
    stf_geom_subarea
    stf_geom_subcatch
    stf_metadata
    stf_fc_flow
    stf_obs_flow 
)

function join_by { local IFS="$1"; shift; echo "$*"; }

# Note: this is only for reference. These modifications will be required:
# - update to flask-SQLalchemy style declaration
# - update 
# - for geom stuff need geoalchemy
sqlacodegen "postgresql://app_user:1234@localhost:5432/stf_db" \
    --tables $(join_by , "${TABLES[@]}") \
    --outfile ./gen_model.py
