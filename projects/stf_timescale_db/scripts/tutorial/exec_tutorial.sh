#!/bin/sh

set -eu

HOST=localhost
USER=postgres
DB=tutorial

psql \
    -h ${HOST} -U ${USER} -d ${DB} \
    --echo-all --password \
    -f tutorial.sql
