TS_DB_NAME:=stf_db
TS_DB_PORT:=5432
AWS_PROFILE:=water-models
STACK_NAME:=stf-prototype-dash-app
EC2_KEYPAIR_NAME:=stf-ec2-keypair
EC2_USER:=ec2-user

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

run-dash-debug:
	cd stf_dash; python index.py

# --- AWS ---
validate-template:
	aws cloudformation validate-template \
		--template-body file://deploy-ec2.yml \
		--profile ${AWS_PROFILE}

deploy-stack:
	aws cloudformation create-stack \
		--stack-name ${STACK_NAME} \
		--capabilities CAPABILITY_IAM \
		--template-body file://deploy-ec2.yml \
		--parameters file://deploy-ec2-params.json \
		--profile ${AWS_PROFILE}

deploy-stack-wait: deploy-stack
	aws cloudformation wait stack-create-complete \
		--stack-name ${STACK_NAME} \
		--profile ${AWS_PROFILE}

update-stack:
	aws cloudformation update-stack \
		--stack-name ${STACK_NAME} \
		--capabilities CAPABILITY_IAM \
		--template-body file://deploy-ec2.yml \
		--parameters file://deploy-ec2-params.json \
		--profile ${AWS_PROFILE}

describe-stack:
	aws cloudformation describe-stacks \
		--stack-name ${STACK_NAME} \
		--profile ${AWS_PROFILE}

stack-outputs:
	aws cloudformation describe-stacks \
		--stack-name ${STACK_NAME} \
		--profile ${AWS_PROFILE} \
		--query 'Stacks[].Outputs' \
		--output table

delete-stack:
	aws cloudformation delete-stack \
		--stack-name ${STACK_NAME} \
		--profile ${AWS_PROFILE}

create-ec2-keypair:
	aws ec2 create-key-pair \
		--key-name ${EC2_KEYPAIR_NAME} \
		--query 'KeyMaterial' \
        --profile ${AWS_PROFILE} \
		--output text > ${EC2_KEYPAIR_NAME}.pem && \
	chmod 400 ${EC2_KEYPAIR_NAME}.pem

ssh-to-ec2:
	@read -p "EC2 DNS/IP: " EC2IP; \
	ssh -o ForwardAgent=yes -A -i "${EC2_KEYPAIR_NAME}.pem" ${EC2_USER}@$$EC2IP
