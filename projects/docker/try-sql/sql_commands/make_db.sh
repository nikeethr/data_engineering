#!/bin/sh

script_path=$(dirname $(readlink -f $0))
. $script_path/run_sql.sh
. $script_path/check_sql_init.sh

# set local_infile=1 on config
run_mysql "SET GLOBAL local_infile=1;"

# create database
run_mysql "CREATE DATABASE $DB_NAME;"
run_mysql "SHOW DATABASES;"

# has to run in 1 command since each command uses a different shell
# also sets local-infile=1 when conecting to server
run_mysql "\
USE $DB_NAME;\
CREATE TABLE pet (name VARCHAR(20), owner VARCHAR(20), species VARCHAR(20), \
sex CHAR(1), birth DATE, death DATE);\
LOAD DATA LOCAL INFILE '$script_path/pet.txt' INTO TABLE pet;" --local-infile=1

run_mysql "USE $DB_NAME; SHOW TABLES; DESCRIBE pet;"
run_mysql "
USE $DB_NAME
SELECT      *
FROM        pet
"
