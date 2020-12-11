AWS_PROFILE:=my-stf-admin
STACK_NAME:=poama-test-ec2-instance
EC2_KEYPAIR_NAME:=poama-test-ec2-keypair
EC2_USER:=ec2-user

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

delete-ec2-keypair:
	aws ec2 delete-key-pair --key-name ${EC2_KEYPAIR_NAME}

ssh-to-ec2:
	@read -p "EC2 DNS/IP: " EC2IP; \
	ssh -o ForwardAgent=yes -A -i "${EC2_KEYPAIR_NAME}.pem" ${EC2_USER}@$$EC2IP
