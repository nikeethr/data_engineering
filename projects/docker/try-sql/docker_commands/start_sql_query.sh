#!/bin/sh

winpty docker run \
    -it \
    --network my-sql-network \
    --rm mysql mysql \
    -h mysql-test \
    -u root \
    -p
