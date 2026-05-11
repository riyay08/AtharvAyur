resource "aws_security_group" "api" {
  name        = "${var.project}-api-sg"
  description = "SSH + API port for AtharvAyur backend"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_ssh_cidr]
  }

  ingress {
    description = "FastAPI"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.api_port_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-api-sg"
  }
}

locals {
  # Amazon Linux 2023: Docker + Compose v2 plugin for ec2-user
  user_data = <<-EOT
    #!/bin/bash
    set -euo pipefail
    dnf update -y
    dnf install -y docker git curl
    systemctl enable --now docker

    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -fsSL "https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-$$(uname -m)" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    usermod -aG docker ec2-user || true

    mkdir -p /home/ec2-user/AtharvAyur
    chown ec2-user:ec2-user /home/ec2-user/AtharvAyur
  EOT
}

resource "aws_instance" "api" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  key_name               = var.ec2_key_name
  vpc_security_group_ids = [aws_security_group.api.id]

  user_data                   = base64encode(local.user_data)
  user_data_replace_on_change = false

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = {
    Name = "${var.project}-api"
  }
}

resource "aws_eip" "api" {
  domain = "vpc"
  tags = {
    Name = "${var.project}-api-eip"
  }
}

resource "aws_eip_association" "api" {
  instance_id   = aws_instance.api.id
  allocation_id = aws_eip.api.id
}
