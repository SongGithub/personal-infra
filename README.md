# take-me-to-the-cloud

[![Build Status](https://travis-ci.org/SongGithub/take-me-to-the-cloud.svg?branch=master)](https://travis-ci.org/SongGithub/take-me-to-the-cloud)

Take me to the cloud before you could take me to the moon


## System design goals

- HA: EC2 instances are spreaded into all 3 Availability Zones in Sydney region, managed by ASG
- Secure:
  - restricts SSH 22 port to separate `jumpbox` access only
- Acknowledged:
  - cloudwatch log integrated
- Easily reproducible. Most infrastructure are coded as templates, which allows it to be recreated as a separate stack with minimal reconfiguration (to `cfn/params/*.yaml`)
- Idempotent. The use of Cloudformation helps with this property

## Initial setup

### CI user setup

To create a CI user in AWS account with codeDeploy permission, locally run following after authenticated to AWS:
- `bin/deploy_cfn cfn iam dev`

Then please go to AWS console, manually create AccessKey. And note the key ID and secret. This is an one-off task
, so simplicity overcomes repeatability. Then follow [instructions](https://docs.travis-ci.com/user/encryption-keys/)

### setup VPC
locally run following after authenticated to AWS:

- `bin/deploy_cfn cfn vpc dev`

- The above script will create a VPC containing 3 public subnets, 3 private subnets
accoss 3 AZ, as well EIP, RouteTables, and NAT

*Note: Infrastructure as code is a good idea but it doesn't mean to put every thing
into build pipeline. Because the pipeline is there to save human operators
from tedious tasks such as repetitive operations to implement incremental changes.
Hence some foundational tasks that are both rarely-happened and high-risk
should be excluded from repeating pipelines. So that no mistake could be
easily made to infrastruture due to a bad code commit. Examples include:
vpc,secrets,and hosted zone etc*

### use of Bastion
- prerequisite: VPC stack is created.
- manully create keypair `sinatra` under AwsConsole/EC2. This action will
downloade a file `sinatra.pem` to your default Download directory,
 for instance `~/Downloads`
- run `chmod 400 ~/Downloads/sinatra.pem`
- run `ssh-add ~/Downloads/sinatra.pem`
- configure cfn/bastion/params/dev.yaml to your CIDR range. It has been locked down to the CIDR rage
- run `bin/deploy_cfn cfn bastion dev` to create CFN stack for bastion
- scale up the bastion ASG to 1
- find public IP of the bastion instance
- `ssh -A ec2-user@<the-bastion-ip>`

*Note: Similarly, creation of the Bastion should not be inside CICD pipeline*
*Note: Please ensure Bastion instance count is 0 after use, also there is a scheduled action that will scale off the Bastion ASG by 6pm everyday for security reason( to prevent cases that operators forgot to do so )*

### EC2/ASG/ELB
- chosen ami: `ami-09b42976632b27e9b`. It is a standard free tier AMI that optimised for ECS
- `bin/deploy_cfn cfn app dev`
- Above script will create ASG for the EC2 instances accross all 3 AZ for high availability purpose,
as well as ELB that will do healh checks on instances


### DNS setup

`dev.sinatra.midu.click` is the current URL for the Sinatra website

Domain `midu.click` is an upstream domain hosted on AWS, and it is in a separate account/hostzone to
Sinatra's one.

Operator needs to:
- create a hostzone `sinatra.midu.click.` at their AWS Route53.
- Apply for hostzone delegation. Send the 4 name servers' address to adminstrator of `midu.click.` to create a NS record in the hostzone
- Wait until the NS record is ready in `midu.click.`. Run `dig sinatra.midu.click` should resolve to
name servers of current hostzone.
- run `bin/deploy_cfn dns dev`. This will create a CNAME record pointing to ELB DNS.

### TLS cert setup

It is designed to use ACM to provision TLS certificate which to be hosted on the ELB. There are 2 steps to do so:
- apply ACM cert with DNS validate method. running script `bin/create_dns_with_cert dev` will ensure a required temporary CNAME record to be created for DNS validateion purpose, and deleted after it is finished.
- add a new Load Balancer Listener to current ELB, in order to enable TLS connection. Simply run `bin/add_lb_listeners dev`. The script will locate existing ACM cert ARN and ELB, and attach it to the new ELB listener.

## CICD setup

### Workflow

- Pack the app inside `app-sinatra/` into a new Docker image and publish with current Build tag to differentiate version
- Rerun CFN stacks to reflect the changes
