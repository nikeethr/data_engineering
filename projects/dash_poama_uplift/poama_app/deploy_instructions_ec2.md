# Deploying the app via EC2

This will be using the AWS console

## 1. Create a VPC to house the EC2 instance

(Or use default)
- The VPC needs to have public subnet

## 2. Create EC2 instance from console

- Go to launch instance menu
```
AWS Console -> EC2 -> Instances -> Launch instances
```

### Configuration

- Select Instance
```
AMI = Amazon Linux 2 AMI 64-bit (x86)
Instance Type = t2.micro
```

- Configure Instance Details
```
Network = Choose created VPC or default
Subnet = subnet-<name> | Default in <region-availability_zone>
Auto-assign Public IP = Enable
```

- Configure Security group

```
Create a new security group.

Update SSH Rule to only allow connection from your IP address:
https://checkip.amazonaws.com/

format=x.x.x.x/32

Add rule for:
    Type=HTTP
    Protocol=TCP
    port=80 
    Source=0.0.0.0/0
```

- Review and launch
    - remember to download the key pair

## 3. Setup docker on EC2 instance

- SSH into instance using key-pair .pem (there should be instructions on the
  EC2 instance)

Run the following commands:

- Update the ec2 instance
```bash
sudo yum update -y
```

- Install docker
https://docs.aws.amazon.com/AmazonECS/latest/developerguide/docker-basics.html
    - Install docker using `amazon-linux-extras`
    - start docker service
    - add default user to docker group
    - you may need to restart your instance after this


- Install docker-compose for linux
    - https://docs.docker.com/compose/install/

- Install git
```bash
sudo yum install git -y
```

- Install python (might not be needed? - good for debugging)
```bash
sudo amazon-linux-extras install python3
```

## 4. Spin-up app

- Clone the repo
```bash
git clone https://github.com/nikeethr/data_engineering.git
cd data_engineering/projects/dash_poama_uplift/
```
- Create `./poama_app/.env-docker-file` with the following:

```bash
POAMA_USER=xxx
POAMA_PASSWD=xxx
DASH_SECRET_KEY=xxx
```

Where, `POAMA_USER`/`POAMA_PASSWD` is the username/password pair
for logging into the app. `DASH_SECRET_KEY` can be generated using:

```bash
python3 -c 'import os; print(os.urandom(16))'
```

- Build and launch the app
```bash
docker-compose up -d
```

or alternatively:
```bash
make up
```

- Launch instance on browser
    - grab ec2 IP off the console and give it a go!

## 5. Terminate instance

Via console:
- Terminate EC2 instance
- Delete key-pair
- Delete security group

> TODO: spin up using IaC e.g. terraform or cloudformation
