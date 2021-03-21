
up:
	docker-compose up -d

down:
	docker-compose down

mongo:
	docker exec -it mongo_db mongo -u root -p 1234

mongo-admin:
	docker exec -it mongo_db mongo admin -u root -p 1234

run-app-local:
	python api/run_hack_api.py

redis-cli:
	docker exec -it redis redis-cli

start-worker-local:
	rq worker hack_test_data

test-sample-data:
	python -m hack_api.test.sample_data

