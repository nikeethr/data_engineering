# Simplified instructions to spin up/tear down/access container shell etc.

CENTOS_BASE_IMG_NAME=c8_base
USER=cylc-user
CNT_CYLC_SUITE_HOST=cylc_suite_host
CNT_CYLC_JOB_HOST=cylc_job_host
NO_LOGIN=/run/nologin

build-centos-base:
	docker build --rm \
		-t local/${CENTOS_BASE_IMG_NAME} \
		./centos_base

build:
	docker-compose build

up-only:
	docker-compose up -d

up: up-only remove-nologin generate-ssh

down:
	docker-compose down

remove-nologin: remove-nologin-suite remove-nologin-job

remove-nologin-suite:
	docker exec ${CNT_CYLC_SUITE_HOST} \
		bash -c '[ -f ${NO_LOGIN} ] && rm ${NO_LOGIN} || echo "already removed"'

remove-nologin-job:
	docker exec ${CNT_CYLC_JOB_HOST} \
		bash -c '[ -f ${NO_LOGIN} ] && rm ${NO_LOGIN} || echo "already removed"'

suite-shell: remove-nologin-suite
	docker exec --privileged --user=${USER} -it ${CNT_CYLC_SUITE_HOST} \
		env TERM="xterm-256color" script -q -c "/bin/bash" /dev/null

job-shell: remove-nologin-job
	docker exec --privileged --user=${USER} -it ${CNT_CYLC_JOB_HOST} \
		env TERM="xterm-256color" script -q -c "/bin/bash" /dev/null

generate-ssh:
	docker exec -it --user=${USER} ${CNT_CYLC_SUITE_HOST} \
		bash -c 'ssh-keygen -t rsa && \
			ssh-copy-id -i ~/.ssh/id_rsa ${CNT_CYLC_JOB_HOST}'

clean-all:
	docker system prune
