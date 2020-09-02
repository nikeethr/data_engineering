# Simplified instructions to spin up/tear down/access container shell etc.

CENTOS_BASE_IMG_NAME=c8_base
USER=cylc-user
CNT_CYLC_SUITE_HOST=cylc_suite_host
NO_LOGIN=/run/nologin

build-centos-base:
	docker build --rm \
		-t local/${CENTOS_BASE_IMG_NAME} \
		./centos_base

build:
	docker-compose build

up:
	docker-compose up -d

up-clean: up remove-nologin

down:
	docker-compose down

remove-nologin:
	docker exec ${CNT_CYLC_SUITE_HOST} \
		bash -c '[ -f ${NO_LOGIN} ] && rm ${NO_LOGIN} || echo "already removed"'

suite-shell: remove-nologin
	docker exec --privileged \
		--user=${USER} \
		-it ${CNT_CYLC_SUITE_HOST} \
		env TERM="xterm-256color" script -q -c "/bin/bash" /dev/null

clean-all:
	docker system prune
