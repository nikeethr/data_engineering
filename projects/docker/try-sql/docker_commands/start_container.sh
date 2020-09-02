#!/bin/sh

base_dir=$(dirname $(dirname $(readlink -f $0)))

# start mysql container and attach bind mount so data can persist
docker run \
    --name mysql-test \
    --mount type=bind,source=$base_dir/sql_db_data,target=/var/lib/mysql \
    --network my-sql-network \
    -e MYSQL_ROOT_PASSWORD=abcd123 \
    -d \
    mysql

# copy sql_commands to container root folder
docker cp $base_dir/sql_commands/ mysql-test:/
