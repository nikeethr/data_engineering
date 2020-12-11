#!/bin/bash -ex

# install things
sudo yum update -y
sudo amazon-linux-extras install docker
sudo yum install docker -y
sudo yum install python3 -y
sudo yum install git -y

# start docker
sudo systemctl enable docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# install docker-compose
sudo curl -L \
    "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# --- run as user ---
# WARNING: This contains some hardcoded scripts/paths assumed from the git repo
# TODO: can probably extract this to a separate script in the repo to be run
# - clone repo
# - start up timescaledb
# - download sample data from s3
# - create virtual env
# - install python requirements
# - run ingestion scripts
# - start up other containers

sudo -u ec2-user bash <<'EOF'
    # clone repo
    cd /home/ec2-user
    git clone https://github.com/nikeethr/data_engineering.git
    cd data_engineering/projects/dash_poama_uplift/spinup_test_ec2_instance

    # setup environment
    /bin/python3 -m venv /tmp/temp_env
    source /tmp/temp_env/bin/activate
    pip3 install -r requirements.txt
    deactivate
EOF

# ---
