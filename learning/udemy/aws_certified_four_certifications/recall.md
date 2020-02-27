# 01-010-010 Introduction to AWS

- This is a very hands-on course
- AWS has powerful hardware and infrastructure situated in various regions
- Some regions provide more services than others.
- We will be using US West Virginia which has 6 accesibility nodes (in case of failure)
- AWS has nice ways to scale up/down based on load
- We need to create an account and we can setup a limit on transfer (e.g. $5)

## Review questions
AWS storage services are listed in the Whitepaper go through them before proceeding..

RDS - relational database service
RDS is not a serverless tech

SES - simple email service
SNS - simple notification service, pub-sub service (many to many)

# AWS White paper
Started by listing a bunch of their storage services

S3 - general purpose scalable, regular frequency read/write (has a low frequency version with low cost), can serve static content, single namespace (i.e. unlike file systems)
Glacier - long term storage (low cost) long retrieval times.
EC2 - used for temporary, scalable storage, can serve dynamic content (that depends on user interaction etc.) 
Cloudfront - cache storage, content delivery network
Snowball - move large amounts of data into/through the cloud
Elastic file system EFS - tree based file system storage (POSIX)

**S3**
- Distribtue static web content (HTTP url/ REST API?)
- Used to host static content
- Used for computational storage (large analytics, financial transactions etc.)
- Backup/archiving critical data -> can then migrate to glacier after a limit

**Glacier**
- Long term storage
- Expected for low retrieval
- Highly secure/encrypted
- Cost per GB/month
- Cost for retrieval
As name suggest it's like a glacier - hard to get into


# 01-010-020 Lab Session - Intro to Storage Services
- Gave overview of various storage services as per paper
- Gave an example architecture within the VPC (virtual private cloud)
    - EBS -> is like storage drive attached to EC2
    - EFS -> is like network drive attached to EC2
    - two servers (EC2) with EBS living in the VPC
    - EFS outside VPC for hierarchical file storage
        - EFS mount within VPC
    - S3 outside VPC for flat data storage, easier solution
        - endpoint to allow traffic to flow in and out of VPC

Direct connect available for fast applications
Snowball for transferring very large amounts of data via physical storage/transport


Loading files into S3:
- Choose region
- create S3 bucket (unique global bucket name)
- upload file to S3 as per file system
- access file (since it's private clicking the URL directly will not do anything)

Cleanup:
- Remove files
- Remove bucket
