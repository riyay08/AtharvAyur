variable "domain_name" {
  type        = string
  description = "Apex domain for the site, e.g. \"atharvayur.com\". The www subdomain is added automatically as a SAN/alias."

  validation {
    condition     = can(regex("^[a-z0-9.-]+\\.[a-z]{2,}$", var.domain_name))
    error_message = "domain_name must be a bare apex domain like \"atharvayur.com\" (no scheme, no www, no trailing slash)."
  }
}

variable "existing_bucket_name" {
  type        = string
  description = "Name of the EXISTING frontend S3 bucket that already holds the built React app (CloudFront origin)."
}

variable "aws_region" {
  type        = string
  description = "Region for the default provider (S3 bucket lookup + bucket policy). CloudFront is global and ACM is pinned to us-east-1 separately."
  default     = "us-east-1"
}

variable "route53_zone_id" {
  type        = string
  description = "OPTIONAL. Route 53 hosted zone ID for domain_name. If set, ACM DNS validation records are created and validation is fully automated. Leave empty (\"\") to validate the certificate manually."
  default     = ""
}

variable "price_class" {
  type        = string
  description = "CloudFront price class. PriceClass_100 = US/Canada/Europe (cheapest); PriceClass_200 adds Asia; PriceClass_All = every edge location."
  default     = "PriceClass_100"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "price_class must be one of: PriceClass_100, PriceClass_200, PriceClass_All."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to every taggable resource via provider default_tags."
  default = {
    Project   = "atharvayur"
    Component = "frontend-https"
    ManagedBy = "terraform"
  }
}
