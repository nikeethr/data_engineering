# Simplified instructions to spin up/tear down/access container shell etc.

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

suite-shell:
	docker exec -it cylc_suite_host \
	env TERM="xterm-256color" script -q -c "/bin/bash" /dev/null

