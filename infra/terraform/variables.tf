variable "aws_region" {
  type        = string
  description = "Region for EC2 + S3 (use same region as your website bucket for simpler IAM)."
  default     = "us-east-2"
}

variable "project" {
  type    = string
  default = "atharvayur"
}

variable "github_org" {
  type        = string
  description = "GitHub org or username that owns the repo."
  default     = "riyay08"
}

variable "github_repo" {
  type        = string
  description = "Repository name (Actions OIDC trust is scoped to this repo)."
  default     = "AtharvAyur"
}

variable "ec2_key_name" {
  type        = string
  description = "Name of an existing EC2 key pair in var.aws_region (create in EC2 console if needed)."
}

variable "admin_ssh_cidr" {
  type        = string
  description = "IPv4 range allowed to SSH to the instance (use YOUR_IP/32, not 0.0.0.0/0 in production)."
  default     = "0.0.0.0/0"
}

variable "api_port_cidr" {
  type        = string
  description = "IPv4 range allowed to reach the FastAPI port (8000) from browsers — start with 0.0.0.0/0; tighten later."
  default     = "0.0.0.0/0"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "existing_s3_bucket_name" {
  type        = string
  description = "Existing frontend bucket Actions will sync into (website hosting already configured on your side)."
}

variable "create_github_oidc_provider" {
  type        = bool
  description = "Set false if this account already has the GitHub OIDC provider (apply will error otherwise — see README import)."
  default     = true
}
