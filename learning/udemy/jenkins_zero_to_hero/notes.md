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
- Select image and begin install, and follow through instructions, choices should be pretty straight forward.
- Download and install PuTTy
- You will need to apt-get a few things via root account
    - `apt-get install -y sudo`
    - `apt-get install -y vim`
    - `apt-get install -y net-tools`
    - `apt-get install -y ssh openssh-server`

Networking:

- Add a host-only adapter (this is required because the private IP generated for VM via NAT does not allow host to connect)
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
