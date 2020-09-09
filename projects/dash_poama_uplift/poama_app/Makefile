CONTAINER_NAME=poama_dash
IMAGE_NAME=poama_dash:latest

build:
	docker build -t ${IMAGE_NAME} .

run:
	docker run \
		-d -p 5000:5000 --name=${CONTAINER_NAME} \
		--env-file .env-docker-file \
		${IMAGE_NAME}

start:
	docker start  ${CONTAINER_NAME}

stop: 
	docker stop ${CONTAINER_NAME}

rm: stop
	docker rm ${CONTAINER_NAME}

clean:
	docker system prune
