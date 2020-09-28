# TODO:
[ ] copy jenkins shell scripts to this git repo


1 - Setup Jenkins
---

Pre-requisites:
- Download VirtualBox (I used 6.1)
- Download OS (I downloaded Debian 10.4, tutorial used CentOS 7)
- !! Uninstall docker as it conflicts with VirtualBox
- Turn off folllowing windows features:
    - Hyper-V
    `bcdedit /set hypervisorlaunchtype off  (turn off)`
    `bcdedit /set hypervisorlaunchtype auto (turn on)`
    - Containers
    - Windows defender, guard etc. 
- Make sure Hardware Virtualization is turned on in BIOS

Setup VM:
- Install virtualbox
- Create new VM (name=jenkins)
- Select image and begin install, and follow through instructions, choices
  should be pretty straight forward.
- Download and install PuTTy
- You will need to apt-get a few things via root account
    - `apt-get install -y sudo`
    - `apt-get install -y vim`
    - `apt-get install -y net-tools`
    - `apt-get install -y ssh openssh-server`

Networking:

- Add a host-only adapter (this is required because the private IP generated
  for VM via NAT does not allow host to connect)
- you will need to assign ip address to the host-only adapter, this can be done via
    - `vim /etc/network/interfaces`
    - add the following:
    ```
    auto <eth_name>
    iface <eth_name> inet dhcp
    ```
    - alternatively you can make it static:
    ```
    iface <eth_name> static
        address 192.168.56.101
        netmask 255.255.255.0
        broadcast 192.168.56.255
    ```
    - you can also set the host address in `/etc/hosts`

## Setup Jenkins

install Docker:

- Follow instructions for debian - https://docs.docker.com/engine/install/debian/
- Add service to run on startup:
    ```sh
        sudo systemctl docker enable
    ```
- Adjust groups so that main user is part of `docker` group:
    ```sh
        sudo usermod -aG docker jenkins
    ```

Setup docker-compose:
- Download docker-compose - https://docs.docker.com/compose/install/:
    ```sh
        sudo curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    ```
    - `uname -s => Linux`
    - `uname -m => x86_64`
- Make sure it is executable:
    ```sh
        sudo chmod +x /usr/local/bin/docker-compose
    ```
    OR
    ```sh
        sudo chmod gu+x /usr/local/bin/docker-compose
        sudo chgrp docker /usr/local/bin/docker-compose
    ```

Get jenkins:
- Get command from docker hub
    ```sh
        docker pull jenkins/jenkins
    ```
- To see images downloaded
    ```sh
        docker images
    ```
- To see where it's stored
    ```sh
        docker info | grep -i root
    ```
- You can then locate the directory e.g. to see how much space it takes
    ```sh
        sudo du -sh /var/lib/docker
    ```

Run jenkins:
- Create `docker-compose.yml` file in `~/jenkins/jenkins-data/`
```yml
version: '3'
services:
    jenkins:
        container_name: jenkins
        # get this from running `docker images`
        image: jenkins/jenkins
        ports:
            # map port 8080 in VM to 8080 in container
            - "8080:8080"
        volumes:
            # folder where jenkins data will persist when container is
            # destroyed, pwd is the docker directory (where the compose file
            # is located)
            - $PWD/jenkins_home:/var/jenkins_home 
        networks:
            # what network to use this service
            - net
        dns:
            - 8.8.8.8
networks:
    # specify a network to create named 'net'
    net:
```

> recall: volume and mount are different. Volume is preferred, but is only
> handled within Docker. Mounts on the other hand can live anywhere within the
> file system and can be accessed by other applications. Which makes it easier
> for some use-cases but adds the risk of corrupting the persistant data.

- Make sure `~/jenkins/jenkins_home` has the proper permissions
    ```sh
        sudo chown -R 1000:1000 jenkins_home
    ```
- Spin up the service
    ```sh
        docker compose up -d
    ```
- Configure jenkins via browser
(note you can find the admin password either using `docker log -f jenkins`
OR `docker exec -it jenkins less <location specified in browser>`)

- Note if things don't install maybe it's because the dns server is not
  referred to properly. Usually docker should pick this up automatically and
  use 8.8.8.8 as one of the DNS resolutions. If this doesn't happen you may
  have to restart docker. e.g. `service docker restart`

Configure local DNS in windows:
- Done for easy access to server using name rather than ip
- Go to C:/Windows/System32/drivers/etc/hosts
- Copy paste IP address of VM created for Host-only connection e.g.
```
192.168.56.101 jenkins.local
```
- Now you can access jenkins via jenkins.local.8080
- you may be able to ssh into it via `ssh jenkins.local` as well.

Handling the docker service:

You may sometimes need to stop/start the service to power off the machine. In
order to persist the data, use `docker-compose stop` to stop the service nad
`docker-compose start` to start it up again where the docker-compose.yml file
is located. `docker-compose down` on the other hand will remove the networks
and volumes permenantly. (Similar to how `docker-compose up` creates these
things.

NOTE: `docker-compose down` will not remove mounted volumes.

2 - Running stuff on Jenkins
---

Navigation
- New item: make a job
- People: users groups etc.
- Build History: task history, performance, success/failuer etc.
- Manager Jenkins: configuration of things e.g. DNS, security credentials etc.
- 

login using admin:1234 user created

A task is pretty much a job... same thing - something that is going to be done.

!!IMPORTANT!!: all the jobs run in the `jenkins` container. Not on the
`jenkins` VM. There are other ways to share data e.g. ssh, volumes, docker in
docker etc. but that's for later.

To get into the bash of the container go:

```
docker exec -ti jenkins bash
```

## Execute first job on Jenkins
- Hit new item
- Freestyle (name it)
- Select build -> shell script
- Type `echo "Hello World"`
- Hit run
- Look at build history
- Sweet!

### Commands
to execute commands wrap around with `$()`
`$(date)`

### redirect output
to redirect output use `>`
`echo "lalala" > `

you can redirect multiple lines using

`()` => subshell OR
`{}` => group of commands (will persist variables)

## Execute shell from jenkins

- Note: container may not come with editor, so you will need to create it
  outside container and then cp it back in.
- Create script e.g. `job-002-shell-script.sh`
- You will need to give it executable permissions
- Use `docker cp job-002-shell-script.sh jenkins:/tmp/` to copy across the
  container
- Add things like user inputs e.g. ($1 and $2 can parse parameters)
- If possible make sure you debug on VM first before putting into container
  (while you have the editor.)
- In the future we can use volumes and build scripts to automatically pass
  resources across to the container on spin up.

## Adding parameters to job

- In general tab of job hit checkbox, project is parameterized.
- The point of parameters is to define these parameters e.g. environment
  parameters for the run (and edit them via UI) within jenkins
- The parameters will be available as env variables which you can access via
  e.g. the bash script.
- If the shell script overwrites based on inputs, you still need to map the
  parameters created in jenkins within the jenkins build!
e.g. within job-xxx.sh:
```
PARAM_1=$1
PARAM_2=$2
# and so on...

# do stuff with params
```

Then calling it in jenkins after defining PARAMS:
```
/tmp/job-xxx.sh $PARAM_1 $PARAM_2 ... $PARAM_N
```
- If you use the environment variables defined by jenkins directly then you
  don't need to specify the parameters to go into the script.

### string parameter
- self explanatory.

### choice parameter
- paramter can only be chosen from a list of options

### logic and booelan parameter
- checked = "true", unchecked = "false"


3 - Jenkins & Docker
---

This is about creating a docker container image instead of VM to get jenkins to
interact with jobs.

Note: This is done using **CentOS** on the Container but we are using Debian on
the main VM. For docker within docker and sharing sock in the jenkins VM
running docker it may be better to keep it with Debian.

While docker-compose.yml orchestrates the running of containers, Dockerfile
inherits image(s) and adds instructions to it on building the image.

Would be good to retry this with:
1. Docker in docker
2. Debian image

## Creating the Docker image

- You will need to create a centos folder where the docker-compose.yml file is
  (I assume we are using this to orchestrate everything)
- You need a `Dockerfile` (note: spelling) for the CentOS image within the
  centos folder.

```dockerfile
  1 FROM centos
  2
  3 # install openssh-server
  4 RUN yum -y install openssh-server
  5
  6 # 1. create remote user
  7 # 2. give remote_user a password
  8 # 3. create home directory + .ssh for remote user
  9 # 4. change permissions of .ssh to allowed permissions (700)
 10
 11 # For centos:7 you will use this line instead to set password:
 12 # echo "1234" | passwd remote_user --stdin && \
 13
 14 RUN useradd remote_user && \
 15     echo "remote_user:1234" | chpasswd && \
 16     mkdir /home/remote_user/.ssh && \
 17     chmod 700 /home/remote_user/.ssh
 18
 19 # Copy generated key as authorized keys
 20 COPY remote-key.pub /home/remote_user/.ssh/authorized_keys
 21
 22 # change owner to remote user
 23 # make sure authorized_key is only r/w via remote_owner
 24 RUN chown remote_user:remote_user -R /home/remote_user/.ssh/ && \
 25     chmod 600 /home/remote_user/.ssh/authorized_keys
 26
 27 # For centos:7 you need to run the following instead:
 28 # RUN /usr/sbin/sshd-keygen
 29 # For later centos:
 30 RUN ssh-keygen -A
 31 # The above will create a key for each key type
 32
 33 # Expose port 22 used for SSH connections
 34 EXPOSE 22
 35
 36 # This should be removed after installation, but doing this just incase to
 37 # allow SSH login
 38 RUN rm -rf /run/nologin
 39
 40 # start the sshd daemon, -D flag specifies that sshd will not detach - which is
 41 # nice for monitoring.
 42 CMD /usr/sbin/sshd -D
```

## RUN

You can think of RUN as the instruction set when building an image. (i.e. these
are used on build time). Dockerfiles `commit` changes to an image based on
changes to the Dockerfile. So the whole image is not re-built. (To prevent
using cached image you can look up how to do this). So only new setup RUN
commands will be built on the image.

You can think of it as adding LAYERS on top of an existing image.

## Generate ssh-key

- Can generate ssh-key using ssh-keygen
- e.g. `ssh-keygen -f remote-key`
- you can set key signature/password as blank
- /usr/sbin/sshd is the deamon that runs the ssh server


## RUN vs. CMD vs. ENTRYPOINT

RUN - adds a layer from the associated command on top of an image to make a new
image.

CMD - the default command (and parameters) run when executing an image. Also
can be used in conjunction with ENTRYPOINT to specify the params of the
entrypoint.

ENTRYPOINT - to be used if the container is run as an executable.

All of the above can be specified in shell form or exec form (json arrays)

## Update docker compose file

We need to update docker-compose file to register the new service that needs to
run.

```yml
services:
    ...
    remote_host:
        container_name: remote-host
        image: remote-host
        build:
            context: centos
        networks:
            - net
```

- container name which will show when run
- image name from the Dockerfile?? (or maybe this defines it if not found)
- build - context, the place to look for where the docker build information
  lives for htis service
- network, same network as jenkins service

## Build
```
docker-compose build
```

Looks through the various services and builds the relevant images.

## Run the service
```
docker-compose up -d
```

will spin up the container(s) that are not running

## Connect to remote host via jenkins container
```
docker exec -it jenkins bash
ssh remote_user@remote_host
```
- note: `remote_host` is like a internal dns created to talk between docker
  services (same as what is defined in the docker-compose.yml file
- needed to remove login file that was created `/run/nologin`

At this point jenkins can talk to the remote server

Note you may need to use `docker-compose up -d` to identify changes in
containers and redeploy.

## setup ssh key to auto connect

- move created remote-key (priv & pub) to jenkins

```
docker cp remote-key jenkins:/tmp/remote-key
```

- you can conect by doing:

```
ssh -i remote-key remote_user@remote_host
```

where `-i` option allows you to provide the identity file

## jenkins plugins (SSH)

- Go to manage jenkins -> plugins and install SSH
- Make sure you have internet connection (otherwise see how to setup the VM in
  001). (Virutalisation may have some issues with wifi conenctions)


Note: I got an error saying reverse proxy setup is broken.
- need to resolve this using https://wiki.jenkins.io/display/JENKINS/Jenkins+says+my+reverse+proxy+setup+is+broken
- for now you can access it using the URI e.g. 192.168.56.101:8080

## note about `net` network

Just because we have ssh configured on the `remote_host` container does not
mean that we can ssh to it from the jenkins VM. This is because the VM itself
don't belong to the network `net`. Only the containers defined in
docker-compose.yml can talk to each other using the protocol as they are in the
same network.


## configure ssh credentials on jenkins

Manage Jenkins -> Manage credentials -> Jenkins -> Add SSH (user with private key)

note this may fail because the generated key may not be RSA...

instead create the key again with `-m PEM` option i.e.

```
ssh-keygen -f remote-key -m PEM
```

Note: You will need to re-configure the authorized key on the remote host

(You could also force a rebuild of the image (or particular layer?))


After this is done

Manage Jenkins -> Configure System -> SSH remote hosts -> Add

Make sure to add the created credentials here and set the hostname (`remote_host`) and port (22)


## Create job using jenkins

Select `Execute shell script on remote host using ssh` under Build
And type in some commands to test. (preferably piping to file so that you can
test the output).
- You will need to select the configured remote host


4 - Jenkins & AWS
---

Purpose: Create a jenkins job to create a mysql backup with amazon S3

## Create SQL service

Add this to the docker-compose file:

```yml
services:
    ...
    db_host:
        container_name: db
        image: mysql:5.7
        volumes:
            - $PWD/db_data:/var/lib/mysql
        environment:
            - MYSQL_ROOT_PASSWORD=1234
        networks:
            - net
```

- need to recreate container using `docker compose up -d`
- mysql takes time to instantiate. you can see this using `docker logs -f db`
- check service is running:
    - `docker exec -it db bash`
    - `mysql --help` for help commands
    - `mysql --user=root --password=1234`
    - `show databases;` to see databases (semi colon is important)
    - `quit;` to quit

## AWS CLI and mySQL Client

We need to install mysql and S3 on remote-host container so that it can take
and grab the backup using the mysql client and push to S3.

We need to adjust the Dockerfile of remote-host to do this.

Note: in the tutorial python (pip) was used for aws cli, but I followed the
latest instructions which required a different approach.

```Dockerfile
# install mysql client
# for server you will need `yum -y install mysql mysql-server`
RUN yum -y install mysql

# install aws cli (needs unzip, groff, glibc, less)
RUN yum -y install unzip
RUN dnf install -y  --enablerepo=PowerTools groff
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install
```

## Setup mySQL db

We are connecting via `remote_host` into `db_host` to create the database.

Note: it's probably better to not use --password=XXXX to avoid bash history
from exposing it.

It may be better to use `-p` and type it out manually
    - `mysql --user=root --host=db_host -p`
    - note: we can do this because it's all in the same network `net` and
      `db_host` is the name of the service

To create the dummy database we need to do some commands.
    - create database
    ```
    mysql> CREATE DATABASE patient_db;
    ```
    - create table
    ```
    mysql> USE patient_db;
    mysql> SHOW TABLES;
    mysql> CREATE TABLE patient(name VARCHAR(20), gender CHAR(1), birth DATE);
    mysql> SHOW TABLES;
    mysql> DESCRIBE patient;
    ```
    - insert entry into table
    ```
    mysql> INSERT INTO patient VALUES ('Isaac', 'M', '1997-03-30')
    ```
    - load from file
    ```
    mysql> LOAD DATA LOCAL INFILE '/path/to/table.txt' INTO TABLE patient
    ```

    ```
    mysql> LOAD DATA LOCAL INFILE '/path/filename.csv' REPLACE
    mysql> INTO TABLE table_name
    mysql> FIELDS TERMINATED BY ','
    mysql> LINES TERMINATED BY '\r\n'
    mysql> (column_name3, column_name5);

    LOCAL - create copy of file of client on server before executing
    REPLACE - replace duplicate items
    COLUMNS - you can specify columns at the end or use the @var to put it into
        a temp variable for pre-processing before doing SET columnx = @varx
    ```
    - list all rows in table
    - select specific elements in table
    - altering table to add primary key to the start of table
    ```
    mysql> ALTER TABLE table_name
    mysql> ADD COLUMN id AUTOINCREMENT PRIMARY KEY FIRST;
    ```
    - Then after follow tutorial try to update DB to perform cleanup:
    https://stackoverflow.com/questions/2630440/how-to-delete-duplicates-on-a-mysql-table


## Create AWS bucket

Pretty straightforward if you have an AWS account.
Simply create a S3 bucket via the console.

Incidentally the command for creating the S3 bucket via CLI is:
```
    aws s3api create-bucket --region xxx --bucket xxx
```

## Create IAM user for authentication into AWS

IAM user configuration required generating a policy for read-only for S3 bucket
that was created.


## Manual SQL backup + upload

Note: we are doing all of this from remote-host

- create mysql backup
```
    mysqldump --host=db_host --user=root -p patients_db > /tmp/patients_db_dump.sql
```

for some reason mysql client is using Ver.8 (probably due to the yum install)
which is causing conflict when dumping the database.

error:

```
    mysqldump: Couldn't execute 'SELECT COLUMN_NAME,
    JSON_EXTRACT(HISTOGRAM, '$."number-of-buckets-specified"')                FROM
    information_schema.COLUMN_STATISTICS                WHERE SCHEMA_NAME =
    'patients_db' AND TABLE_NAME = 'patient_info';': Unknown table
    'COLUMN_STATISTICS' in information_schema (1109)
```

To get around it we need to set `--column-statistics=0`

You may need to revisit this if you still get an error when loading the DB back
into the server.

Note: the dump is saved in `remote_host` not `host_db`

- configure aws access key/secret using environment variables
(this is the simplest way, but maybe not the safest.)

https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html

```
    export AWS_ACCESS_KEY_ID=xxx
    export AWS_SECRET_ACCESS_KEY=xxx
    export AWS_DEFAULT_REGION=ap-southeast-2
```

- upload to aws using s3 cp or sync

```
    aws s3 cp /tmp/patients_db.sql s3://<insert-s3-bucket-here>/patients_db_dump.sql
```

specify `--dryrun` flag to test

## Create auto backup db

see: `s5-resources/db_backup.sh`

run:

```
    ./db_backup.sh db_host patients_db 1234
```

## Setup secure keys in Jenkins

Jenkins -> credentials -> System -> Global credentials

Kind = Secret Text

Things to define:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `MYSQL_PASSWD`

- Need to setup build step on ssh host (under Build)
- Need to add credentials to variables (under Build environment)
- Optionally specify parameters e.g. `db_host` and `db_name` (Under Project is parameterized)

Still couldn't run build because parameters were somehow not passed to the
shell script

Had to specify env when passing the credentials to `remote_host`
```
    env \
    AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
    AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
    DB_PASSWD=$DB_PASSWD \
    /tmp/scripts/db_backup.sh $DB_HOST $DB_NAME
```

interestingly in jenkins logs it blocks out these credentials.


## Script deleted!

!IMPORTANT: When doing `docker compose down` all scripts/things stored
temporarily get wiped out. So you will need to create a workdir volume or mount
to persist these.


Jenkins & Ansible
---

## Install Ansible in Docker

- Need to create a jenkins container with ansible installed.

- Needed to change USER to root so that ansible can be installed and then back to
USER jenkins again

- Used pip to install ansible so that it is independent of the linux distro.

## Make SSH permenant within jenkins container

- Using volumes to do this... since they are persistent

- create ansible folder within `jenkins_home` directory

- move remote key within centos container to the `jenkins_home/ansible` folder

- note that you cannot spin up a container when you are within the
  `jenkins_home` directory in the VM due to permission issues.

- The safe way to do this is probably to tear down the container and then copy
  over stuff.

## Ansible inventory

- create ansible hosts configuration to connect into `remote_host` via ansible

According to ansible:

> **Inventory**
> A list of managed nodes. An inventory file is also sometimes called a
> “hostfile”. 

Which alludes to why the config is called an inventory.

Strucutre:

```yml
---
namespace:
    hosts:
        host1:
            ...
        host2:
            ...
        ...
    vars:
        ...
```

Some useful things:

```yml
- ansible_host        # name of host/ip
- ansible_user        # user to connect with
- ansible_connection  # e.g. ssh
- ansible_private_key_file  # e.g. private ssh key file to allow automation

```

Ping:

```bash
    ansible -m ping -i hosts.yml test1
```

## First playbook

Playbook simply has the a yml definition with which infrastructure (hosts) to
use for particular tasks. And the definition of the tasks themselves which are
predefined commands (and yml like structure) that ansible can parse and
construct a command.

Note: for a particualr playbook you need to run playbook with
`ansible-playbook` not just `ansible`.

Structure:

```yml
---
# task group
- name: taskgroup1
  hosts:
    ...
  tasks:
    - name: task1
      command:
        ...
    - name: task2
      ...
    ...
- name: taskgroup2
  ...
...

```

Run:

```bash
    ansible-playbook -i hosts.yml play.yml
```

So far:

- inventory - definition of infrastructure (inventory items) to use
- playbooks - definition of tasks to associated to above inventory items
