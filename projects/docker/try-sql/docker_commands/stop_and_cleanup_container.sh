#!/bin/sh

# remove db
docker exec mysql-test sh ./sql_commands/drop_db.sh

# stop and remove volumes associated with container
docker container stop mysql-test
docker container rm  --volumes mysql-test
