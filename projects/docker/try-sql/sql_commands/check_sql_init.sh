#!/bin/sh

script_path=$(dirname $(readlink -f $0))
. $script_path/run_sql.sh

# sleep until sql is initialised
echo "checking sql initialisation..."
until $(run_mysql "SHOW DATABASES;" >/dev/null 2>&1); do
    eval "$check_sql"
    sleep 0.1
done;
echo "...mysql initialised on image!"
