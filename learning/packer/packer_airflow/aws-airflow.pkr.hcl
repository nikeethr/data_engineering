packer {
  required_plugins {
    amazon = {
      version = ">= 0.0.2"
      source  = "github.com/hashicorp/amazon"
    }
  }
}


variable "ami_prefix" {
  type    = string
  default = "packer-airflow"
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
}

source "amazon-ebs" "centos" {
  ami_name      = "${var.ami_prefix}-${local.timestamp}"
  instance_type = "t3.medium"
  region        = "ap-southeast-2"
  source_ami    = "ami-03d56f451ca110e99"
  ssh_username  = "centos"
}

build {
  name = "airflow-dev"
  sources = [
    "source.amazon-ebs.centos"
  ]

  provisioner "file" {
    source      = "${path.root}/files/"
    destination = "/tmp"
  }

  provisioner "shell" {
    script = "${path.root}/files/install_airflow_dependencies.sh"
  }

  provisioner "shell" {
    execute_command = "chmod +x {{ .Path }}; sudo -H -iu airflow bash -c '{{ .Vars }} {{ .Path }}'"
    script = "${path.root}/files/install_airflow.sh"
  }

  provisioner "shell" {
    inline = [
      "sudo cp /tmp/airflow.sh /home/airflow",
      "sudo cp /tmp/airflow-webserver.service /etc/systemd/system",
      "sudo cp /tmp/airflow-scheduler.service /etc/systemd/system",
      "sudo systemctl enable airflow-webserver.service",
      "sudo systemctl enable airflow-scheduler.service",
      "sudo chown airflow:airflow /home/airflow/airflow.sh"
      "sudo chmod +wrx /home/airflow/airflow.sh"
    ]
  }
}
