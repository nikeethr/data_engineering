Virtual Box
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

Setup Jenkins in VM using Docker:

