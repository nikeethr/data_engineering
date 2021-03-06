# Cylc playground

This will document my process in setting up a playground using a linux VM +
docker

Note: If you can do this with docker straight-away without creating users in
the linux VM.

## Instructions

TODO

## Examples

TODO


# Background notes:

## Tasks

- [x] Create cylc user on VM
- [x] Make notes document
- [x] cylc-suite-host: Setup Dockerfile with instructions (this will take some
    trial and error)
    - [x] Start with compatible OS and executing bash as the entry point
    - [x] Create cylc user
    - [x] Create docker-compose file to handle build/spin-up/teardown
    - [x] Configure ssh to access docker directly
    - [x] Makefile to simplify commands
    - [x] Go through instructions to install cylc and update/rebuild Dockerfile
        as you go. Layer caching should prevent you from having to do everything
        several times.

## Reading

- Example docker file (ubuntu and maybe outdated):
    https://github.com/alanbchristie/cylc-docker/blob/master/docker/Dockerfile
- Simple development environment with Docker:
    https://www.integralist.co.uk/posts/dev-environments-within-docker-containers/
- Cylc:
    https://cylc.github.io/doc/built-sphinx/index.html
- Rose:
    https://metomi.github.io/rose/doc/html/index.html
- docker-compose + Makefile:
    https://medium.com/freestoneinfotech/simplifying-docker-compose-operations-using-makefile-26d451456d63
- running gui apps in docker
    http://fabiorehm.com/blog/2014/09/11/running-gui-apps-with-docker/
- ssh into docker
    https://stackoverflow.com/questions/28134239/how-to-ssh-into-docker
    https://stackoverflow.com/questions/48235040/run-x-application-in-a-docker-container-reliably-on-a-server-connected-via-ssh-w

## Create cylc user in linux VM

- cylc user needs ability to run docker commands in order to launch containers.

### Create user + groups
```bash
# add group
sudo groupadd cylc

# add user and add to jenkins/docker group to do docker stuff
sudo useradd -g cylc -G jenkins,docker cylc-user

# change the password of cylc user
sudo passwd cylc-user

# create home directory for user
sudo mkhomedir_helper cylc-user

# cp .vimrc from jenkins
cp /home/jenkins/.vimrc /home/cylc-user/.vimrc

# change ownership of .vimrc
sudo chown -R cylc-user:cylc .vimrc
```

You will then have to change the shell of the user to /bin/bash

```bash
$ ssh cylc-user@hostname
$ chsh
Password:
Changing the login shell for cylc-user
Enter the new value, or press ENTER for the default
        Login Shell [/bin/sh]: /bin/bash
```

## Setting up container for cylc-suite host

### Base image

Needed to set `stdin_open` and `tty` in order to keep container running
initially.

```Dockerfile
version: '3'
services:
    cylc_suite_host:
        container_name: cylc_suite_host
        image: cylc/suite_host
        stdin_open: true
        tty: true
        build:
            context: ./cylc_suite_host
        networks:
            - cylc_net
networks:
    cylc_net:
```

## Configure ssh

There's a few things I needed to do here for docker side to work:
- install ssh-clients and ssh-server
- install xauth for authorizing XServer connections
- setup a cylc-user in the container (0700 for .ssh directory and 600 for files)
- Install GraphicMagick because Centos8 doesn't have ImageMagick
- Allow for X11 forwarding (needed to copy across a X11 file)
- Make sure to setup port mapping for 22 from the container to (some available port) in the VM
- Finally copy over the pn image using scp
- ssh (-AY) (-p with the opened port) into the cylc-user within the container
- display the image using the appropriate command

On the windows side I needed an X-server:
- I used `vcxsrv` on recommendation
- Needed to configure the windows host see below

### Windows: known host varying due to container regeneration

!IMPORTANT: everytime I recreated the image I had to delete the known-hosts in windows

In order to prevent this I added the following in ~/.ssh/config:

```
Host jenkins.local
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
XAuthLocation "C:\Program Files\VcXsrv\xauth.exe"
```

I also had to add the following to the `.bash_profile` in git bash on my
windows machine
```
export DISPLAY=127.0.0.1:0.0
```

## Docker container:

Needed to add the following line to DockerFile:

```
RUN echo "X11UseLocalhost no" >> /etc/ssh/sshd_config
```


### scp image to container

```
scp -P 52022 display.png cylc-user@jenkins.local:~
```

### ssh into container

```
ssh -AY -p 52022 cylc-user@jenkins.local
```

### Configure without ssh-server running???

TODO: 
https://stackoverflow.com/questions/48235040/run-x-application-in-a-docker-container-reliably-on-a-server-connected-via-ssh-w


## Install Cylc

### Requirements

- Python
```
dnf install python2 python2-devel python2-pip
```
- OpenSSL
```
dnf install openssl
```
- pyOpenSSL
```
pip install pyopenssl
```
- python-requests
```
pip install requests
```

**Checkpoint**
Now check the following imports:
- urllib3: `import urllib3`
- PyGTK: `import gtk`

gtk didn't work so I had to look back at the cylc reference docker
- I used dnf to install various things (e.g. pygtk2, and python2-devel)
- gtk also complained about this:
    ```
    Gtk-WARNING **: Locale not supported by C library. Using the fallback 'C' locale.
    ```
    installing locale libraries (centos specfic):
    ```
    yum install -y langpacks-en langpacks-de glibc-all-langpacks
    ```

- Graphviz
```
dnf install graphviz
```

- Pygraphviz
```
dnf install graphviz-dev
pip install pygraphviz==1.2
```

- All python requirements:
```
mock
pyopenssl
requests
cherrypy==6.0.2
jinja2 == 2.10
pygraphviz==1.2
sphinx>=1.53,<1.7.9
```

- Also installed
    - vim
    - sudo
    - systemd
    - gcc

**Checkpoint**

- needed to include PowerTools for dnf in order to install some things
```
RUN dnf -y install dnf-plugins-core && \
    dnf config-manager --set-enabled PowerTools
```

### Installing from repo

clone repo:
https://github.com/cylc/cylc-flow.git

checkout tag: 7.8.6

Followed instructions to install from tarball


## Configuring cylc

Following through the cylc docs (see: Reading)


- global config file as per instructions in `less /opt/cylc/etc/global.rc.eg`

```
cylc get-global-config > /opt/cylc/etc/global.rc
```

- setting up environment in job hosts (to be revisited)

- configure Cylc Review
Apache
```
dnf install mod_wsgi httpd
systemctl enable httpd.service
```

adhoc
```
setsid cylc review start 0</dev/null 1>/dev/null 2>&1 &
```
(runs on 8080 - need port mapping in docker-compose)

Added adhoc version to `docker_entrypoint.sh`


## Examples

- Note: openssl 1.1.x (used by 19,x,x) not supported by cylc so I installed
  pyopenssl=18.0.0

