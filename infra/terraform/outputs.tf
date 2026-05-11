output "api_public_dns" {
  description = "Point VITE_API_URL at http://THIS:8000 (or put HTTPS proxy in front)."
  value       = aws_eip.api.public_dns
}

output "api_public_ip" {
  value       = aws_eip.api.public_ip
  description = "Elastic IP attached to API instance."
}

output "aws_deploy_role_arn" {
  description = "Set GitHub repo variable AWS_DEPLOY_ROLE to this ARN."
  value       = aws_iam_role.github_actions_deploy.arn
}

output "frontend_bucket" {
  value       = data.aws_s3_bucket.frontend.bucket
  description = "S3_BUCKET GitHub Actions variable."
}

output "bootstrap_ssh_hint" {
  description = "One-time server setup."
  value       = "ssh -i YOUR_KEY.pem ec2-user@${aws_eip.api.public_dns}   # clone repo → backend/.env → docker compose per docs"
}
