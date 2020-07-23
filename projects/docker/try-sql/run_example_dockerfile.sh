#!/bin/sh

cnt_name=mysql-test-cnt
base_dir=$(dirname $(readlink -f $0))
pushd $base_dir

docker build --tag mysql-test-img:1.0 . 

# run
winpty docker run \
    -it \
    --name $cnt_name \
    --mount type=bind,source=$base_dir/sql_db_data,target=/var/lib/mysql \
    --network my-sql-network \
    -d mysql-test-img:1.0

# Note: running the container should print out some messages

# docker exec mysql-test-cnt sh ./sql_commands/drop_db.sh

# stop and remove volumes associated with container
docker container stop $cnt_name
docker container rm  --volumes $cnt_name

popd
