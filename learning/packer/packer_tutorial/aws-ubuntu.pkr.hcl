# required plugins by HashiCorp e.g. AMI builder
packer {
  required_plugins {
    amazon = {
      version = ">= 0.0.2"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

# variables are good use em, also they are not really "variables" more like
# constants.

# this is an input variable
# they can be configured in multiple ways (environment var, tvars file, cli)
variable "ami_prefix" {
  type    = string
  default = "learn-packer-linux-aws-redis"
}

# local variables.
# these assign a name to an expression so they can be used several times. can
# be used multiple times within a module
# Can be good to avoid repeatablility but sometimes can be overkill so need to
# know the right tradeoff.
locals {
  # remove characters: "- TZ: from timestamp as they are not allowed"
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
}

# source is necessary when using a plugin outside the HashiCorp domain
# image is created from amazon-ebs source
source "amazon-ebs" "ubuntu" {
  # you could also provide alternative credientials/profile here
  # https://www.packer.io/docs/builders/amazon#authentication
  # ami names must be unique
  ami_name      = "${var.ami_prefix}-${local.timestamp}"
  instance_type = "t2.micro"
  region        = "us-west-2"
  # Note: exactly one AMI has to be returned, most recent returns the latest
  # created image.
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/*ubuntu-xenial-16.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    # filters images by owner
    owners = ["099720109477"]
  }
  # packer will ssh to instance using temporary credentials to provision the
  # instance (in this case ubuntu is sudo, otherwise it may be ec2-user
  # depending on the AMI)
  # TODO: not quite sure how to launch the EC2 instance after the fact
  # - I guess we specify the key pair on the terraform instance resource
  # later...
  ssh_username = "ubuntu"
}

# what should packer do after it launches
build {
  name = "learn-packer"
  # The reference source is the ubuntu source (similar convention to terraform
  # to refer to resources)
  sources = [
    "source.amazon-ebs.ubuntu"
  ]

  # provisioners are executed in order
  provisioner "shell" {
    environment_vars = [
      "FOO=hello world",
    ]
    inline = [
      "echo Installing Redis",
      "sleep 30",
      "sudo apt-get update",
      "sudo apt-get install -y redis-server",
      "echo \"FOO is $FOO\" > example.txt",
    ]
  }

  provisioner "shell" {
    inline = ["echo This provisioner runs last"]
  }
}
