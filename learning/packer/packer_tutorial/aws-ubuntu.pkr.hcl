# required plugins by HashiCorp e.g. AMI builder
packer {
  required_plugins {
    amazon = {
      version = ">= 0.0.2"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

# source is necessary when using a plugin outside the HashiCorp domain
# image is created from amazon-ebs source
source "amazon-ebs" "ubuntu" {
  # you could also provide alternative credientials/profile here
  # https://www.packer.io/docs/builders/amazon#authentication
  ami_name      = "learn-packer-linux-aws"
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
}
