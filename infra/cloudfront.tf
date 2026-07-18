locals {
  s3_origin_id = "s3-${var.existing_bucket_name}"

  # When DNS validation is automated we depend on the validation resource so
  # CloudFront only attaches a fully-issued certificate. Otherwise we use the
  # certificate ARN directly (it must already be validated out-of-band).
  certificate_arn = var.route53_zone_id != "" ? aws_acm_certificate_validation.this[0].certificate_arn : aws_acm_certificate.this.arn
}

# Reference the already-existing frontend bucket (not managed/created here).
data "aws_s3_bucket" "frontend" {
  bucket = var.existing_bucket_name
}

# AWS-managed caching policy tuned for static sites (long TTLs, gzip/brotli).
data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

# Origin Access Control (OAC) is the modern replacement for Origin Access
# Identity. It lets CloudFront authenticate to a PRIVATE S3 bucket using SigV4,
# so the bucket no longer needs public website hosting or public-read policies.
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "oac-${var.existing_bucket_name}"
  description                       = "OAC for ${var.existing_bucket_name} frontend origin"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "HTTPS frontend for ${var.domain_name}"
  default_root_object = "index.html"
  price_class         = var.price_class

  # Serve the site from both the apex and the www subdomain.
  aliases = [var.domain_name, "www.${var.domain_name}"]

  origin {
    domain_name              = data.aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = local.s3_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    target_origin_id       = local.s3_origin_id
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    cache_policy_id = data.aws_cloudfront_cache_policy.caching_optimized.id
    compress        = true
  }

  # --- Single Page Application routing ---
  # With a private S3 origin, a request for a client-side route (e.g. /dashboard)
  # has no matching object, so S3 returns 403 (and 404 for ListBucket-enabled
  # buckets). Rewrite both to index.html with a 200 so React Router can take over.
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = local.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

# Grant the distribution (and only this distribution) read access to the bucket
# via the OAC. This REPLACES the bucket's existing policy — after migration the
# bucket can be fully private (Block Public Access on, static website hosting off).
data "aws_iam_policy_document" "frontend_oac" {
  statement {
    sid     = "AllowCloudFrontOACRead"
    effect  = "Allow"
    actions = ["s3:GetObject"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    resources = ["${data.aws_s3_bucket.frontend.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = data.aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_oac.json
}
