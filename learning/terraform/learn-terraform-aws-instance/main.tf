# terraform configuration
terraform {
  backend "s3" {
    bucket = "learning-terraform-state-nr"
    key    = "single_server_example/terraform.tfstate"
    region = "ap-southeast-2"
  }

  required_providers {
    aws = {
      # the provider that we want to add
      source = "hashicorp/aws"
      # ~> operator allows increments of the rightmost minor version
      # Do not use with multiple templates as it can cause issues.
      version = "~> 3.27"
    }
  }

  # required version of terraform
  # >= greater than or equal to certain version
  required_version = ">= 0.14.9"
}

# AWS provider configuration
# can provide alternate providers using alias and each resource/module etc. can
# select the provider based on "provider" item or "providers" list
provider "aws" {
  profile = "default"
  # note: Our default region is ap-southeast-2 we can test if this overrides
  # that.
  # region = "us-west-2"
  region = "ap-southeast-2"
}

data "local_file" "public_key" {
  filename = "${path.module}/id_ed25519.pub"
}

resource "aws_key_pair" "wsl2_ubuntu_sentry" {
  key_name   = "wsl2_ubuntu_sentry"
  public_key = data.local_file.public_key.content
}

# resource configuration
# aws_ => we are looking at the aws provider, and 'instance' is the associated
# resource (ec2 instance). The name given to this for reference is 'app_server'
resource "aws_instance" "app_server" {
  ami           = "ami-06b1edd7c6d35cf22"
  instance_type = "t3.medium"
  tags = {
    Name = "AirflowCondaExperimental"
  }
  associate_public_ip_address = true
  key_name                    = "wsl2_ubuntu_sentry"
  depends_on = [
    aws_key_pair.wsl2_ubuntu_sentry,
  ]
}

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app_server.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}
