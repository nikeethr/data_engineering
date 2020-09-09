CONTAINER_NAME=poama_nginx
IMAGE_NAME=poama_nginx:latest

build:
	docker build -t ${IMAGE_NAME} .

run:
	docker run -d -p 80:5001 --name=${CONTAINER_NAME} ${IMAGE_NAME}

start:
	docker start  ${CONTAINER_NAME}

stop: 
	docker stop ${CONTAINER_NAME}

rm: stop
	docker rm ${CONTAINER_NAME}

clean:
	docker system prune
