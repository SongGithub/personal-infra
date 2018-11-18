[![Build Status](https://travis-ci.org/SongGithub/take-me-to-the-cloud.svg?branch=master)](https://travis-ci.org/SongGithub/take-me-to-the-cloud)

# take-me-to-the-cloud


> Take me to the cloud before you could take me to the moon


## System design goals

- HA: EC2 instances are spreaded into all 3 Availability Zones in Sydney region, managed by ASG
- Secure:
  - restricts SSH 22 port to separate `jumpbox` access only
- Acknowledged:
  - cloudwatch log integrated
- Easily reproducible. Most infrastructure are coded as templates, which allows it to be recreated as a separate stack with minimal reconfiguration (to `cfn/params/*.yaml`)
- Idempotent. The use of Cloudformation helps with this property
- Ease of deployment. Code for both application and infrastructre is automatically deployed through Travis machine user, once pushed to master branch.
- Simplicity. The Sinatra app is packaged in Docker image which comes with all unnecessary dependencies installed in a minimal operating system. Plus, the docker image has been size-optimised by containing only binaries for installed dependencies. (Temporary files for installation have been disgarded during Docker image build)

## Initial setup

### CI user (IAM) setup (Manual deploy)

To create a CI user in AWS account with codeDeploy permission, locally run following after authenticated to AWS:
- `bin/deploy_cfn cfn iam dev dev`

Then please go to AWS console, manually create AccessKey. And note the key ID and secret. This is an one-off task
, so simplicity overcomes repeatability. Then follow [instructions](https://docs.travis-ci.com/user/encryption-keys/)

### setup VPC (Manual deploy)
locally run following after authenticated to AWS:

- `bin/deploy_cfn cfn vpc dev dev`

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
- run `bin/deploy_cfn cfn bastion dev dev` to create CFN stack for bastion
- scale up the bastion ASG to 1
- find public IP of the bastion instance
- `ssh -A ec2-user@<the-bastion-ip>`

*Note: Please ensure Bastion instance count is 0 after use, also there is a scheduled action that will scale off the Bastion ASG by 6pm everyday for security reason( to prevent cases that operators forgot to do so )*

### ECR (Manual deploy)
- `bin/deploy_cfn cfn ecr dev dev`

### EC2/ASG/ELB
- chosen ami: `ami-09b42976632b27e9b`. It is a standard free tier AMI that optimised for ECS
- `bin/deploy_cfn cfn app dev dev`
- Above script will create ASG for the EC2 instances accross all 3 AZ for high availability purpose,
as well as ELB that will do healh checks on instances


### DNS setup

[https://dev.sinatra.midu.click](https://dev.sinatra.midu.click) is the current URL for the Sinatra website

Domain `midu.click` is an upstream domain hosted on AWS, and it is in a separate account/hostzone to
Sinatra's one.

Operator needs to:
- create a hostzone `sinatra.midu.click.` at their AWS Route53.
- Apply for hostzone delegation. Send the 4 name servers' address to adminstrator of `midu.click.` to create a NS record in the hostzone
- Wait until the NS record is ready in `midu.click.`. Run `dig sinatra.midu.click` should resolve to
name servers of current hostzone.
- run `bin/deploy_cfn dns dev dev`. This will create a CNAME record pointing to ELB DNS.

### TLS cert setup

It is designed to use ACM to provision TLS certificate which to be hosted on the ELB. There are 2 steps to do so:
- apply ACM cert with DNS validate method. running script `bin/create_dns_with_cert dev` will ensure a required temporary CNAME record to be created for DNS validateion purpose, and deleted after it is finished.
- add a new Load Balancer Listener to current ELB, in order to enable TLS connection. Simply run `bin/add_lb_listeners dev`. The script will locate existing ACM cert ARN and ELB, and attach it to the new ELB listener.

## Assumptions
- When the build pipeline is running, none of the Cloudformation stacks should be in `IN_PROGRESS` status

## Short-commings/TO-DOs
- Permissions given to the CI user could be narrowed down. It has been given full-access to many types of resources.
- EC2 instance type could be further refined to provide a more suitable and cheaper option.
- The way docker image version get passed into EC2 instance could be simpler.
- Param setup for Cloudformation templates forces me to repeat myself again and again, and it contains uncessary params otherwise it would complain. It could be swapped out entirely with other template engines such as Gomplate.
