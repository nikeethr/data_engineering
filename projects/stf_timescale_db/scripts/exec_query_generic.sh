#!/bin/sh

SCRIPT_NAME="$0"
usage() {
    echo "usage: "${SCRIPT_NAME}" [database_name] [sql_query_path]"
}

if [ "$#" -lt 2 ]
then
    usage >&2
    exit 1
fi

set -eu

HOST=localhost
USER=postgres
DB=$1
SQL_QUERY_PATH=$2

psql \
    -h ${HOST} -U ${USER} -d ${DB} \
    --echo-all --password \
    -f ${SQL_QUERY_PATH}
