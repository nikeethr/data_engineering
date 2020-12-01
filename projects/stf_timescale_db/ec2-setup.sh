#!/bin/bash -ex

# install docker
sudo yum update -y
sudo amazon-linux-extras install docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# install docker-compose
sudo curl -L \
    "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# TODO:
# - git
# - update tsdb image to initialize tables
# - download git dir
# - start docker service for tsdb
# - check that it worked
# - install python packages & tools for ingestion scripts
# - store ingest data in s3 bucket
# - update ingestion scripts to source from s3
# - run ingestion scripts
# - check db
