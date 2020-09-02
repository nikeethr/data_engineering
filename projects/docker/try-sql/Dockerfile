# build image from sql
ARG VERSION=latest
FROM mysql:$VERSION

# set workdir
WORKDIR /work

# set environment variables
ENV MYSQL_ROOT_PASSWORD abcd123

# copy relevant data files
COPY ./sql_commands /work/sql_commands

# volume
# - host directory must be specified at runtime
VOLUME ["/var/lib/mysql"]

# run db setup - this should happen after the docker container is running...
# if we really want to do this we will have to bind this to CMD
# RUN ["sh", "/work/sql_commands/check_sql_init.sh"]
# RUN ["sh", "/work/sql_commands/make_db.sh"]

# cmd/entrypoint
# not specified: use default entrypoint from sql: e.g. https://github.com/docker-library/mysql/blob/f7ba980b846fa5fd97423997e5ea0675600b185a/8.0/Dockerfile

ENTRYPOINT ["/bin/sh", "-c", "echo hello"]
