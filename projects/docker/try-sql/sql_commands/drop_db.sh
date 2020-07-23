#!/bin/sh

script_path=$(dirname $(readlink -f $0))
. $script_path/run_sql.sh

run_mysql "DROP DATABASE IF EXISTS $DB_NAME;"
