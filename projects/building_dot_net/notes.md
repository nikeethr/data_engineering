# Building .net apps

This will cover:
- c# .net 4. whatever (requires msbuild)
- .net core (requires dotnetcore)

## TODO


2020-08-30
- [x] install dotnetcore
- [x] create dotnetcore app sample
- [x] upload to github (+.gitignore)
- [x] create user in jenkins VM + env
- [ ] create ssh key for easy github access
- [ ] partial git pull command
- [ ] create docker file for dotnetcore 2.1
    [ ] get file from gitlab
    [ ] build app
    [ ] run app
- [ ] Test it out

backlog
- [ ] convert project to dotnet core with only the alg stuff
- [ ] test hello-world example (learn the docker instructions well)

## Resources

https://blog.sixeyed.com/dockerizing-net-apps-with-microsofts-build-images-on-docker-hub/

- docker in docker
https://tutorials.releaseworksacademy.com/learn/the-simple-way-to-run-docker-in-docker-for-ci

## dotnetcore .gitignore

Git ignore for .netcore taken from:
https://raw.githubusercontent.com/OmniSharp/generator-aspnet/master/templates/gitignore.txt

## Create sample App

Followed steps here:
https://dotnet.microsoft.com/learn/dotnet/hello-world-tutorial/intro

(note: used dotnet 2.1.517)

```
$ dotnet new console -o myApp
$ dotnet run
```

This will run the helloworld app

## Create user in jenkins

(Similar to cylc). Let's see if I remember

```sh
# make group for user
sudo groupadd corsonys

# add user to corsonys group (-g)
# - and give it jenkins/docker group permissions (-G)
# - create home directory (-m)
# - set shell (-s)
sudo useradd -g corsonys -G jenkins,docker -m --shell=/bin/bash corsonys-user

# set password
sudo passwd corsonys-user

# copy .vimrc instructions
sudo /home/jenkins/.vimrc /home/corsonys-user/.vimrc
sudo chown -R corsonys-user:corsonys .vimrc
```

## Generate ssh key

https://docs.github.com/en/github/authenticating-to-github/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent

to generate:
```
$ ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

You will need to install ssh/git see:
https://vsupalov.com/build-docker-image-clone-private-repo-ssh-key/
https://stackoverflow.com/questions/18136389/using-ssh-keys-inside-docker-container

## Partial git pull

```
git clone <URL> --no-checkout <directory>
cd <directory>
git sparse-checkout init --cone # to fetch only root files
git sparse-checkout set apps/my_app libs/my_lib # etc, to list sub-folders to checkout
# they are checked out immediately after this command, no need to run git pull
```

## Create docker file to pull 
