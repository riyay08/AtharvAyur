terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Default provider — used for the S3 bucket lookup, bucket policy, and the
# (global) CloudFront distribution itself.
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# CloudFront ONLY trusts ACM certificates that live in us-east-1 (N. Virginia),
# regardless of where the rest of your infrastructure runs. This aliased
# provider forces the certificate (and its DNS validation) into that region.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = var.tags
  }
}
