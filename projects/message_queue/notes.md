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
