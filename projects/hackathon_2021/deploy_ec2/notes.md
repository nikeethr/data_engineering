1. modify template and scripts are required
2. generate key pair: `make create-ec2-keypair`
3. generate payload: `./generate_deploy_params.sh`
4. validate template: `make validate-template`
5. deploy stack: `make deploy-stack`
6. describe stack to see status (but this is better on console): `make describe-stack`
7. ssh to ec2 to see what's happening: `make ssh-to-ec2`
8. clean up: `make delete-stack`
