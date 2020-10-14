# Deploying the app to EB

Note: these instructions are tested on Linux (Debian 10)

## 1. Install EB CLI

See: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html

I installed it using pip: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install-linux.html

The way I did it was using a conda environment, to keep things neat (virtualenv
is an alternative if there's no conda):

```sh
conda create -n ebcli python=3.7
conda activate ebcli
pip install awsebcli
```

## 2. EB Init

Navigate to code checkout and run:

```sh
eb init -i
```

or alternatively:

```sh
make eb-init
```

This will give you an interactive prompt to initialise EB for your application.
See example at the end of: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb3-init.html

We want the following configuration:

```
region = ap-southeast-2 (Sydney)
application name = poama_dash_app_poc
aws credentials = <enter aws access id and aws secret key>
platform = docker
platform_branch = Docker running on 64bit Amazon Linux 2
create ssh for instances = Y  # helpful for ssh into the EC2 instances
```

For the aws credentials it may be good to create a user policy and use that
user's credentials rather than your own.
See: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/AWSHowTo.iam.managed-policies.html

## 3. Configure environment variables

- Create `.ebextensions` directory in the base directory of the code checkout 
- Create a environment config file: `.ebextensions/environment.config`

Populate the file with the following (replacing the `xxx`):

```
option_settings:
    aws:elasticbeanstalk:application:environment:
        POAMA_USER: xxx
        POAMA_PASSWD: xxx
        DASH_SECRET_KEY: xxx
```

Where, `POAMA_USER`/`POAMA_PASSWD` is the username/password pair
for logging into the app. `DASH_SECRET_KEY` can be generated using:

```bash
python3 -c 'import os; print(os.urandom(16))'
```

## 4. EB Create

Spins up the infrastructure on AWS to run the application.

Note: for eb create/deploy/terminate the following arbitrary envrionment name
is used:

```sh
EB_ENV=poama-dash-uplift-poc
```

Run:

```sh
eb create ${EB_ENV} --instance-types t2.micro --single
```

or alternatively:

```sh
make eb-create
```

This will create a single EC2 instance application so no load balancer
attached. This may mean that it's less durable (and may not take too much load)
but it's a dev app so it should be okay. Advisable to use load balancer in
production.

Creation may take some time - you can login to the AWS console to check it's
status.

## 5. EB Deploy

Deploys updates to the application. Normally the application is part of a git
repo in which you can automate deployment based on a particular branch.  But
for our purpose we are just keeping it simple by doing a adhoc deployment.

Note: you don't have to run deploy after the first `eb create`. It's only
needed for subsequent updates (e.g. code changes).

Run:

```sh
eb deploy ${EB_ENV} --staged
```

or alternatively:

```sh
make eb-deploy-staged
```

## 6. EB Terminate/Restore

Stops the app and removes any linked infrastructure from AWS.


```sh
eb terminate ${EB_ENV}
```

or alternatively:

```sh
make eb-terminate
```

It is possible to restore the application without needing to re-create it by
running `eb restore` and choosing the environment to restore.

Note: to remove the environement completely you may need to manually remove the
S3 bucket used to store artefacts/configs and deploy the code .
