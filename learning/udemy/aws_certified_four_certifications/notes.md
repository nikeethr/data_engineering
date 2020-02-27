# 01-010-010 Introduction to AWS

## What is the cloud?
- World wide data centres
- On-demand delivery of IT resources
- Scalable on-demand
- Various product categories
    - Compute
    - Storage
    - Database
    - Machine Learning
    - etc...
- Reduced cost, No Capital investment in infrastructure

## AWS Global Infrastructure
- Available in various Geographic Regions
- Using N. Virginia for this course, since it has the most products available
- Location is important to optimize latency, minimise costs, regulatory reasons etc.

### Availablility sones
- Regions divided into (>=2) availability zone.
- This is so that if one availability zone goes down others can pick up the slack.
- N. Virginia has 6 availability zones.
- Connected together via high speed fibre optic network.

## Edge locations
- Cloudfront CDN cached at edge locations.
    - high performance delivery.
    - DDOS protection.

## AWS Management Console
- Web interface to AWS.
- Monitoring costs.

## SDK & CLI Access
- For AWS as backend.
- Also able to access using HTTP REST API.
- CLI control multiple AWS services from command line and automation through scripts.

## Whitepaper: AWS Storage Solutions

### Amazon Simple Storage (S3)
**Description**
- General purpose storage, durable and highly scalable at low cost.
- 0 - 5TB data objects
- concurrent read/write

**Offerings**
- S3 Standard: general purpose
- S3 Standard-IA: long-lived, less frequently accessed
- Amazon Glacier: low-cost archival data

**Usage Patterns**
1. store and distribute static web content and media
2. host entire static websites
3. data store for computation, large-scale analytics, financial analysis etc.
    - access available from multiple compute nodes
4. backup and archiving critical data.
    - can move cold data to Glacier using rules

Doesn't suit all file structures:
- S3 is flat namespace
- Not structured (e.g. no SQL support)
- Not for rapidly changing data (that require small read write latency)
- Encrpyting/archiving data - better with Glacier
- Dynamic web hosting (no database interaction/server side scripting etc.)

**Performance**
- EC2 -> S3 is fast if same region
- usage scaling for large number of users
- multi-part upload
- common pattern is to pair S3 with CloudSearch/DynamoDB/RDS. S3 stores actual
  data, database stores metadata.
- S3 Transfer Acceleration to reduce latency (using CloudFront to route traffic
  more efficiently)

**Durability and Availability**
- Data stored over multiple devices and facilities in selected region
- Error correction built in and no single point sof failure
- Can sustain concurrent loss of data in two facilities
    - 99.999999999% durability per object
    - 99.99% availability over the whole year
- can enable cross-region to automatically copy data asynchronously in
  different regions

**Scalability and Elasticity**
- virtually unlimited files per bucket
- unlimited amount of size (bytes)

**Security**
- can write an access policy to manage access
- server-side encryption or client-side encryption available
- versioned
- Multi factor authentication for delete (MFA)
- Access loggign

**Interfaces**
- REST web API
- Can emulate file structure by naming objects based on file heirarchy
- SDK wrappers e.g. python, nodejs, ruby etc.
- AWS CLI
- Management Console to create buckets upload/download
- Configure to receive notification (SNS)

**Cost Model**
- Only pay for storage used
- Components:
    1. storage (GB/month)
    2. transfer in/out (GB/month)
    3. requests (every 1000/month)
    4. Additional fees for transfer acceleration (only charged if provides a benefit)

## Glacier
Extremely low-cost storage service 0.007$/GB/month

Data stored in archives, single file or several files.

Retrieving archives requires initiation of a job


**Usage patterns**
Archiving offsite enterprise information, media assets, resaerch/ scientific
data. Magnetic tape replacement

Use EBS/RDS/EFS etc. for rapid changes
Use S3 for immediate access as jobs take 3-5 hours in Glacier.

**Performance**
- take 3-5 hours to retrieve
- multipart uploading  up to 40 TB
- range retrievals by specifying portion of arrchive.

**Durability**
11 nines on archive
reduntantly stores data in several facilities before returning SUCCESS.
AWS performs regular integrity checks. (self-healing)

**Scaling**
Single archive up to 40TB, but no limit for total number of archives.

**Security**
- Only you can access.
- IAM for other people to access.
- Server side or client side encryption.
- lock vaults for long-term records.
- AWSCloudTrail to monitor access.

**Interfaces**
API SDK etc.
Monitor status usign SNS.
Retrieved object is in RRS for a short retention period.

**Cost model**
storage per month
transfer per month
requests per month

Can retrieve up to 5% of average monthly storage for free.
