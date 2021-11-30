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
  region = "us-west-2"
}

# resource configuration
# aws_ => we are looking at the aws provider, and 'instance' is the associated
# resource (ec2 instance). The name given to this for reference is 'app_server'
resource "aws_instance" "app_server" {
  ami           = "ami-830c94e3"
  instance_type = "t2.micro"
  tags = {
    Name = "MyExampleAppServer"
  }
}
