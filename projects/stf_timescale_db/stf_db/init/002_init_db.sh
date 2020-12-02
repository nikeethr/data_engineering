#!/bin/bash
set -e

DB_NAME=stf_db
USER_PASSWD=1234
USER_NAME=app_user
TABLE_INIT_PATH=/tmp/init_tables.sql

# create database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE ${DB_NAME};
EOSQL

# connect to db and setup user, setup extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    CREATE EXTENSION IF NOT EXISTS postgis;

    CREATE USER ${USER_NAME}  WITH PASSWORD '${USER_PASSWD}';

    GRANT CONNECT ON DATABASE ${DB_NAME} TO ${USER_NAME};

    GRANT USAGE ON SCHEMA public TO ${USER_NAME};

    GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${USER_NAME};

    ALTER DEFAULT PRIVILEGES IN SCHEMA public
       GRANT SELECT ON TABLES TO ${USER_NAME};
EOSQL

# run default script
psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$DB_NAME" \
    -f ${TABLE_INIT_PATH}
