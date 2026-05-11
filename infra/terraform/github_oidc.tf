# Allows GitHub Actions in this repo to assume a role via OIDC (no long-lived AWS keys in GitHub secrets).
# If your account already has this provider (common), set create_github_oidc_provider=false and run:
#   terraform import 'aws_iam_openid_connect_provider.github[0]' arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com
# …or remove this resource block and paste the existing provider ARN into a data source — see README.

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 1 : 0

  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
  ]
}

locals {
  github_oidc_arn = (
    length(aws_iam_openid_connect_provider.github) > 0
    ? aws_iam_openid_connect_provider.github[0].arn
    : "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
  )
}

resource "aws_iam_role" "github_actions_deploy" {
  name = "${var.project}-gha-deploy-${var.aws_region}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = local.github_oidc_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
      }
    }]
  })

  tags = {
    Name = "${var.project}-github-actions-deploy"
  }
}

resource "aws_iam_role_policy" "github_actions_deploy_s3" {
  name = "${var.project}-s3-deploy"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
        ]
        Resource = data.aws_s3_bucket.frontend.arn
      },
      {
        Sid    = "Objects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
        ]
        Resource = "${data.aws_s3_bucket.frontend.arn}/*"
      },
    ]
  })
}
