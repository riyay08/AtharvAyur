output "cloudfront_distribution_domain_name" {
  description = "The xxxx.cloudfront.net domain. Point your DNS (apex + www) at this via an ALIAS/CNAME, or test the site here before cutting DNS over."
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront's hosted zone ID — use as the target zone for Route 53 ALIAS A/AAAA records mapping your domain to the distribution."
  value       = aws_cloudfront_distribution.frontend.hosted_zone_id
}

output "cloudfront_distribution_id" {
  description = "Distribution ID — use for cache invalidations (aws cloudfront create-invalidation --distribution-id ...)."
  value       = aws_cloudfront_distribution.frontend.id
}

output "acm_certificate_arn" {
  description = "ARN of the issued ACM certificate (us-east-1) attached to the distribution."
  value       = aws_acm_certificate.this.arn
}
