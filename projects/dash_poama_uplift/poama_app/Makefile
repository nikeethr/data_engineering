CONTAINER_NAME=poama_dash
IMAGE_NAME=poama_dash:latest
EB_ENV=poama-dash-uplift-poc

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

eb-init:
	eb init -i

eb-create:
	eb create ${EB_ENV} --instance-types t2.micro --single

eb-deploy:
	eb deploy ${EB_ENV}

eb-terminate:
	eb terminate ${EB_ENV}

eb-restore:
	eb restore

eb-ssh:
	eb ssh ${EB_ENV}
