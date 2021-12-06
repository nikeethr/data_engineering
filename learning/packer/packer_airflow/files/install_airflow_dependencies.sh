#!/bin/bash

# environment installations
sudo yum -y install wget tar gzip gcc make expect sqlite

# install sqlite
# NOTE: not needed for rhel as we'll be using auroradb
# ---
# NOTE: This should already be installed on the default centos
# wget https://www.sqlite.org/src/tarball/sqlite.tar.gz --no-check-certificate
# tar -xzf sqlite.tar.gz
# cd sqlite/
# export CFLAGS="-DSQLITE_ENABLE_FTS3 \
#     -DSQLITE_ENABLE_FTS3_PARENTHESIS \
#     -DSQLITE_ENABLE_FTS4 \
#     -DSQLITE_ENABLE_FTS5 \
#     -DSQLITE_ENABLE_JSON1 \
#     -DSQLITE_ENABLE_LOAD_EXTENSION \
#     -DSQLITE_ENABLE_RTREE \
#     -DSQLITE_ENABLE_STAT4 \
#     -DSQLITE_ENABLE_UPDATE_DELETE_LIMIT \
#     -DSQLITE_SOUNDEX \
#     -DSQLITE_TEMP_STORE=3 \
#     -DSQLITE_USE_URI \
#     -O2 \
#     -fPIC"
# export PREFIX="/usr/local"
# LIBS="-lm" ./configure --disable-tcl --enable-shared --enable-tempstore=always --prefix="$PREFIX"
# make
# make install
# ---

# create airflow user
sudo groupadd airflow
sudo useradd -g airflow airflow


