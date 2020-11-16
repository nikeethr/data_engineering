TS_DB_NAME:=stf_db
TS_DB_PORT:=5432

# container postgres shell
# (connect via separate docker command from within container)
cnt-psql:
	docker exec -it ${TS_DB_NAME} psql -U postgres

# host postgres shell (connect from host)
host-psql:
	psql -h localhost -p ${TS_DB_PORT} -U postgres -W 

# bash into db
db-sh:
	docker exec -it ${TS_DB_NAME} bash

# clean up artefacts
clean: down
	docker system prune

# spin up
up:
	docker-compose up -d

# tear down
down:
	docker-compose down

# clean up all docker containers
# Warning: THIS WILL REMOVE ALL UNUSED RESOURCES BUT WILL FREE SPACE
clean-all:
	docker system prune --all

run-api-debug:
	cd stf_api/experimental; python run_stf_api.py
