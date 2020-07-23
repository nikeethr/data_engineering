# Docker Engine

## pull image from docker

```
docker pull mysql
```

## create network
```
docker network create my-sql-network
```

## run sql container

>> (runs on bridge network - docker0)
```
docker run \
    --name mysql-test \
    --mount type=bind,source=`pwd`/sql_db_data,target=/var/lib/mysql \
    --network my-sql-network \
    -e MYSQL_ROOT_PASSWORD=abcd123 \
    -d \
    mysql
```
## Connect to MySQL

### Via a different container instance
```
winpty docker run \
    -it \
    --network my-sql-network \
    --rm mysql mysql \
    -h mysql-test \
    -u root \
    -p
```


### Used as a client

>> TODO: not complete

```
docker run -it --rm mysql mysql -hsome.mysql.host -usome-mysql-user -p
```

# SQL

## Create database
```
create database db;
```

## Use the database
```
use db;
```

## Create a table
```
create table foo <schema>

where schema is like (<variable> <type>, ...) 

e.g.

create table foo (name VARCHAR(20), dob DATE);
```

## show/describe table

```
show tables;
describe foo;
```
