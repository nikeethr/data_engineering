# Configure SSH

## Store credentials

**Security -> Manage Credentials -> Add Credentials -> SSH Username with private key ->**

Add in the private key for remote host there.

## Configure remote host

**System Configuration -> Configure System -> SSH remote hosts -> Add**

Setup remote host with private key.

# Job

**Build -> Execute shell script on rmemote host using SSH**

Refer to remote host here.

```sh
NAME=Nikeeth
echo "Hello, $NAME. Current date and time is $(date)" > /tmp/remote-file
```
