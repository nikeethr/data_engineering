# Module 1
## Logistics
- books @ https://online.vitalsource.com/ (login with gmail) - lasts for 730 days download
- qwiklabs


## What is cloud
- Datacenter, servers routers etc. off premesis
- Accessed via the internet
- AWS owns the resources, they provision the resources.
- Modularised hardware that is linked together


## Cloud deployment models
- On premisis
- Hybrid (e.g. frontend in cloud, other resources are on-prem)
    - e.g. banks etc., with core databases sitting on prem
    - but want to use cloud for scalability of front-end applications
- Cloud
  - Born in the cloud - e.g. AirBnB, dropbox etc.
  - If your application fails, just turn it off

## Benefits

### Trade capital expense for variable expense
  - CapEx -> OpEx


### Massive economics of scale
  - Pricing keeps reducing over time due to mass ordering. (72 times so far)
  - Daily adding of infrastructure equivilent to a fortune 500 company in 2009
  - AWS gets a competitive price


### Stop Guessing Capacity
  - Auto scaling
  - e.g. bushfires where demand changes during different periods


### Increase speed and agility
  - too much bureaucracy for hardware (government)
  - Just need a PO#


### Stop spending money on running/maintaining datacentres
  E.g. Navjot had a macbook when he started. Then Apple launched a new one a
  few months later. Navjot tried to ask IT to change, but it was already
  provisioned.

  AWS ability to stick to hardware component or upgrade seemlessly

  You're paying for a lot of things:
    - Electricity
    - Land/Space
    - etc. etc.

  Increased focus on the application that is focused on.


### Go global in minutes
  Ability to deploy in multiple regions

  Canva
  - graphic design application
  - started in Sydney
  - Now operating in 119 countries


### AWS Security
  - Keep your data safe
  - Meet compliance requirements
    - aws.amazon.com/compliance
    - aws.amazon.com/artifact/ to get certificates of compliance
  - Save money
  - Scale quickly


### AWS service categories
  - Lots of categories (23)
  - Including Satellite!


## AWS global infrastructure
  - infrastructure.aws
  - region is a geographic location where the datacentre is located
  - lines are optical fibre cables

### Availability
  - region table: aws.amazon.com/about-aws/global-infrastructure/regional-product-services/

### Edge locations
  - Not full fledged data centres but hold caching data, firewall, NAT

### Brief AWS console showcase
  - Login to aws - top right
  - Support/getting started resources
  - Docs if you are stuck somewhere
  - Important to check region you are deploying a instance to
  - Always signs in from region you sign out from
  - Event log (designed for failure)
  - Spinbar for favourite instances. (Based on browser)


### Three ways to access AWS
  - AWS management console (one time)
  - AWS CLI (for devs)
  - SDKS to integrate with software

  Also there's a mobile app for aws console

#### CLI download
  - aws.amazon.com/cli/
  - aws shell, autocomplete etc.

#### AWS SDKs
  - Can be integrated to several languages

## Questions
Patrick
  - containerised app: https://aws.amazon.com/getting-started/hands-on/deploy-docker-containers/
Richard
  - helicopter view of what is available
  - https://aws.amazon.com/blogs/aws/author/jbarr/
Patrick
  - certification: https://aws.amazon.com/certification/certified-cloud-practitioner/


# Module 2

## Cloud journey

Divided between foundational services and platform service
e.g. if request EC2 (foundational) it is your responsibility to keep it up to
date patched etc.
- you have root access

Managed services
- underlying resources managed by AWS (Cloud Native)
- no root access, accessed via APIs


## EC2

Elastic compute cloud. Any server (game/file/etc.), but sitting on top of a
hypervisor.

Hypservisor - a software that creates a computer from available hardware
resources. Shared resources (virtual sliced).

Hypervisor has different configurations:
- c, t, m etc.

https://aws.amazon.com/ec2/instance-types/

t instance type - CPU is a shared pool resource.

AMI: Operating system


There are restrictions - so that services are delivered optimally.
E.g. if I launch 50 VMs, it will not be allowed. (Service limits - based on consumption).

https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html
- could be automatic (if reasonable based on consumption)
- but suppose you ask for 100,000 EC2 instances then this will have to go
through capacity planning.

Account -> service quota

Bootstrapping (on restart)
User data (on cloud init)
  ```
      #!/bin/bash
      yum install ...
  ```

Highly available 4 nines 99.99%

Use latest generation always - better price to performance ratio

Can't hot add ram
No automatic storage

### Space (SAM)
EBS
- 1 - 16 TB connected over a network.
- When EC2 is shut down, still paying for EBS storage
- can only be linked to 1 EC instance
- need to copy data to other availability zones (backup)
- block storage, files split into evenly sized blocks of data, with it's own
address

S3
- copied across several availbiilty zone
- highly available
- indexed global unique identifier (key-value) + metadata
- objects are stored in objects (must be accessed as a whole)
- need to make it public via access key
- 99.99... (11 9s) durable
- https://aws.amazon.com/s3/sla/
- can configure lifecycle - to move old data to e.g. Glacier (cold storage)

EFS
- multiple availability zones

## Virtual Private cloud

Public subnet - internet gateway
Private subnet


## Security groups

Security groups are stateful - they will always let responses back out if they came in

AWS managed services are regional e.g. S3 not limited to availability zone
EC2 are limited to availability zone

### Benefits
  - Elasticity: change instance type

# Module 3: Building in the Cloud

## Improving your initial project
  - S3: static content
  - EC2
    - EBS: database files
    - Instance store

## CloudWatch
  - Free
  - Setup alarms
  https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/mon-scripts.html

e.g. memory utilization not shown since hypervisor doesn't have access to OS.


## Why scaling matters
Demand changes over time. You don't have to pay for the auto-scaling (so always
have one in case of crashes) => It will swap available zone e.g. if you keep
instances to 1 and it goes down.

### Autoscaling
- min = 2
- max = 10
- desired = 6 -> manual configuration changes

Can be deployed accross availability zones
Reference architecture e.g. with 10 EC2 instances

AZ1: EC2 x 5
AZ2: EC2 x 5

AZ - availability zone

Features:
1. Autoscaling group
2. Launch configuration (what type of instances should be there)

### Load balancer

Application vs Network load balancer.

What are the 7 layers of network:

Application layer
Presentation Layer
Session

Network layer TCP/IP
Network Layer

Data link
Physical


#### Application load balancer
- directs different urls to different applications running on a EC2 instance

### Network load balancer
- directs traffic to TCP port - OS needs to decouple network packet and deliver
to application.


## Database services
Database on top of EC2 instances
- Aurora
- MySQL
- Postgres
etc.

Dynamodb is scalable

Redshift data warehouse

DocumentDB - MongoDB

Neptune graph based database (many to many relationships)

## Cloud formation
yaml file to define your resources (can use tools to map this out visually)

## Elastic beanstalk
resources provisioned for you

## Direct connect
Can talk to service providers to direct connect via ISP

## Route 53
How to distribute the data (via domain registration).
DNS server
- configure health checks
- route traffic to the domain

Netflix this is my architecture:
  https://www.youtube.com/watch?v=WDDkLOT8SCk

## EFS
Shared file repository can be shared via EC2 instances


## Media services - streaming applications

## lambda
Function as a code (firecracker OS)
https://aws.amazon.com/blogs/aws/firecracker-lightweight-virtualization-for-serverless-computing/

based on trigger use boto3 (for example) to retrieve data e.g. from S3

## Amazon SNS pub - sub

trigger lambda
http notification/ email etc.


## Cloudfront
Cache data for applications near your users.

# Module 4: Security

Shared responsiblity model
- hardware configurations security - AWS
- security in the cloud (configuration of the resources being deployed)
    - bucket policies etc.
    - subnet etc.
- Unmanaged services (EC2, EBS)
    - firewall, os patching etc. etc.
- Managed services (RDS, S3, DynamoDB)
    - firewall etc. handled
    - need to manage bucket policies etc.

## IAM
Authentication/authorization of resources

## Amazon inspector
Check vulnerability

## protect from DDoS
AWS uses a black watch for itself.
For AWS front end - e.g. cloudfront/load balancer etc. will be protected by default
  - AWS Shield is a managed service which is always on

## AWS Compliance
Can be downloaded from
  - aws.amazon.com/compliance

For exams - understand the difference of Security IN the Cloud from Security OF the Cloud

## Pricing

--- TODO ---
Download ebooks
