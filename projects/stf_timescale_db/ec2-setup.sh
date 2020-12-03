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
    cd data_engineering/projects/stf_timescale_db

    # spin up stf database
    /usr/local/bin/docker-compose up -d stf_db

    # get data from s3
    /bin/bash get_sample_data_from_s3.sh

    # prepare python environment for ingesting netcdf/csv data via psycopg
    cd scripts/stf_ingest
    /bin/python3 -m venv /tmp/temp_env
    source /tmp/temp_env/bin/activate
    pip3 install -r requirements.txt

    # ingest metadata csv file
    python3 ingest_meta.py

    # ingest netcdf files
    python3 ingest_stf_flow.py

    # copy and ingest shp files directly from docker
    docker cp sample_data stf_db:/tmp/
    docker cp ingest_shp_files_docker.sh stf_db:/tmp/
    docker exec stf_db /tmp/ingest_shp_files_docker.sh

    # create materialized view for faster geom access for shp files
    docker exec -i stf_db psql -U postgres -d stf_db < views.sql

    # spin up other containers
    cd /home/ec2-user/data_engineering/projects/stf_timescale_db
    /usr/local/bin/docker-compose up -d
EOF

# ---
