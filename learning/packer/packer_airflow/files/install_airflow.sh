#!/bin/bash

set -x

whoami
env

# install conda on airflow user
wget https://repo.anaconda.com/miniconda/Miniconda3-py38_4.10.3-Linux-x86_64.sh -O /home/airflow/miniconda.sh
bash /home/airflow/miniconda.sh -b -p /home/airflow/miniconda
export PATH="${PATH}:/home/airflow/miniconda/condabin"

# initialise and activate conda
__conda_setup="$('/home/airflow/miniconda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
eval "$__conda_setup"
conda env create -f /tmp/environment.yml
conda activate tpaws

# install airflow into conda env using pip
AIRFLOW_VERSION=2.1.0
# For example: 3.7
PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-no-providers-${PYTHON_VERSION}.txt"
# For example: https://raw.githubusercontent.com/apache/airflow/constraints-2.1.0/constraints-no-providers-3.7.txt
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# TODO: for RHEL setup
# pip install psycopg2

# setup config file
# TODO

# init db (use sqlite for now)
airflow db init

# add user to db
airflow users create \
    --username admin \
    --password airflow \
    --firstname airflow \
    --lastname admin \
    --role Admin \
    --email airflow_dev@airflow.com

# start webserver
# Note: this should go in services/system.d
# airflow webserver --workers=2 -D


# start scheduler
# Note: this should go in services/system.d
# airflow scheduler -D

# TODO: test all of this in redhat in BoM as it may vary from centos
