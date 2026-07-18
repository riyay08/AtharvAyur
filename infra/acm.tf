# Public SSL/TLS certificate for the apex domain + www subdomain.
#
# IMPORTANT: provider = aws.us_east_1 forces this certificate into N. Virginia,
# which is the only region CloudFront will read certificates from.
resource "aws_acm_certificate" "this" {
  provider = aws.us_east_1

  domain_name               = var.domain_name
  subject_alternative_names = ["www.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# --- Automated DNS validation (only when a Route 53 zone ID is provided) ---
#
# ACM emits one CNAME record per distinct name on the certificate. We create
# each one in the hosted zone so ACM can confirm domain ownership without any
# manual steps. If route53_zone_id is empty, no records are created and you
# must add the validation CNAMEs at your DNS provider yourself.
resource "aws_route53_record" "cert_validation" {
  for_each = var.route53_zone_id != "" ? {
    for dvo in aws_acm_certificate.this.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  } : {}

  zone_id         = var.route53_zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

# Blocks until ACM observes the validation records and issues the certificate.
# Only created when DNS validation is automated via Route 53; otherwise validate
# the certificate manually before referencing it from CloudFront.
resource "aws_acm_certificate_validation" "this" {
  count    = var.route53_zone_id != "" ? 1 : 0
  provider = aws.us_east_1

  certificate_arn         = aws_acm_certificate.this.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
