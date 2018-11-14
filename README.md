# take-me-to-the-cloud
Take me to the cloud before you could take me to the moon
[![Build Status](https://travis-ci.org/SongGithub/take-me-to-the-cloud.svg?branch=master)](https://travis-ci.org/SongGithub/take-me-to-the-cloud)
## System design goals

- HA: EC2 instances are spreaded into all 3 AZ zone in Sydnet region, managed by ASG
- Secure:
  - locked down ports
  - restrict SSH 22 port to separate bastion access only
- Acknowledged:
  - cloudwatch log integrated


## Initial setup

### CI user setup

To create a CI user in AWS account with codeDeploy permission, locally run following after authenticated to AWS:
- `bin/deploy_cfn cfn iam dev`

Then please go to AWS console, manually create AccessKey. And note the key ID and secret. This is an one-off task
, so simplicity overcomes repeatability. Then follow instructions [here](https://docs.travis-ci.com/user/encryption-keys/)



locally run following after authenticated to AWS:
- `bin/deploy_cfn cfn dns dev`
- `bin/deploy_cfn cfn vpc dev`

*Note: Infrastructure as code is a good idea but it doesn't mean to put every thing
into build pipeline. Because the pipeline is there to save human operators
from tedious tasks such as repetitive operations to implement incremental changes.
Hence some foundational tasks that are both rarely-happened and high-risk
should be excluded from repeating pipelines. So that no mistake could be
easily made to infrastruture due to a bad code commit. Examples include:
vpc,secrets,and hosted zone etc*


## EC2
chosen ami: `ami-09b42976632b27e9b`. It is a standard free tier AMI that contains Ruby


## use of Bastion
- prerequisite: VPC stack is created.
- manully create keypair `sinatra` under AwsConsole/EC2. This action will
lead to a file `sinatra.pem` downloaded to your default Download directory,
for instance `~/Downloads`
- run `chmod 400 ~/Downloads/sinatra.pem`
- run `ssh-add ~/Downloads/sinatra.pem`
- configure cfn/bastion/params/dev.yaml to your CIDR range. It has been locked down to the CIDR rage
- run `bin/deploy_cfn cfn bastion dev` to create CFN stack for bastion
- scale up the bastion ASG to 1
- find public IP of the bastion instance
- `ssh -A ec2-user@<the-bastion-ip>`
*Note: Similarly, creation of the Bastion should not be inside CICD pipeline*
