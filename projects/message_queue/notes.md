# Create RabbitMQ project

## Setup

- Created docker-compose file to run rabbit mq
- default login for management console is guest:guest
- you can add these to the env to change it:
    - `RABBITMQ_DEFAULT_USER`
    - `RABBITMQ_DEFAULT_PASS`
- However for non-localhost connections e.g. VMs (in this case) we will need to
  configure users with definitions file
- Used the following commands to create users/dump the config file (and then
  mounted it on the volume):

```
rabbitmqctl add_vhost ${VHOST}
rabbitmqctl add_user ${USER} ${PASS}
rabbitmqctl set_user_tags ${USER} administrator
rabbitmqctl set_permissions -p ${VHOST} ${USER} ".*" ".*" ".*"
rabbitmqctl export_definitions definitions.json
```


## Example 1

- Used console app
- Renamed to add Send (Publish) & Receive (Consume) projects
- Installed RabbitMQ package (5.X) using:
```sh
    dotnet add package RabbitMQ.Client --version 5
```
- Used 5.X because that's compatible with .NET Core 2.1




# Dotnet core app


## Database

### Scaffolding

This process is used to template a data model based on existing database. e.g.

```sh
dotnet ef dbcontext scaffold "server=localhost;port=3306;user=root;password=mypass;database=sakila" MySql.Data.EntityFrameworkCore -o sakila -t actor -t film -t film_actor -t language -f
```

See: https://dev.mysql.com/doc/connector-net/en/connector-net-entityframework-core-scaffold-example.html

TODO: is it possible to have a common model referred to by multiple projects...

### Migration

This process is to update/migrate the database assuming the data model is maintained by the app.


# Celery

## Installation

https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html

## Conda

Created conda env named `celery` and installed the following:
```
celery
sqlalchemy
mysql-connector-python
gevent
```

mysql-connector-python latest version needed as using MySQL 8.0 we need support
for `caching_sha2_password`.

Also installed `mysql-client` on debian using the following:
https://www.digitalocean.com/community/tutorials/how-to-install-the-latest-mysql-on-debian-10

## Results database
