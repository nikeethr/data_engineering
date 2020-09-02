#!/bin/sh

script_path=$(dirname $(readlink -f $0))

# start container
sh $script_path/docker_commands/start_container.sh

# execute sql commands

# sleep until container is up and running
echo "waiting for container to run..."
while [[ "$(docker inspect -f {{.State.Running}} mysql-test)" != "true" ]]; do
    sleep 0.1;
done;
echo "...container running!"

# sleep until sql is initialised
echo "checking sql initialisation..."
check_sql="docker exec mysql-test sh ./sql_commands/check_db.sh >/dev/null 2>&1"
until eval "$check_sql"; do
    eval "$check_sql"
    sleep 0.1
done;
echo "...mysql initialised on container!"

echo "creating db..."
docker exec mysql-test sh ./sql_commands/make_db.sh
echo "...done!"

# cleanup and remove container
echo "clean up and remove container..."
mount=$(docker inspect --format='{{range .Mounts}}{{.Source}}{{end}}' mysql-test)
"Note: sql data unrelated to the example db still persists on bind mount \
however.\nDelete ${mount} manually using rm command."

sh $script_path/docker_commands/stop_and_cleanup_container.sh
echo "...(almost)all gone!"

