# Terraform — bootstrap EC2 API + GitHub OIDC → S3

This lives in your repo so **you** (or CI) apply it against **your** AWS account. We cannot apply it from Cursor on your behalf.

## What gets created

- **EC2** (Amazon Linux 2023) with **Elastic IP**, security group (**22** SSH + **8000** FastAPI).
- **User-data** installs **Docker** and **Compose v2** and creates `/home/ec2-user/AtharvAyur`.
- **IAM OIDC provider** for `token.actions.githubusercontent.com` (unless it already exists in the account — see below).
- **IAM role** `AtharvAyur` workflows can assume to **sync assets to your existing S3 bucket** (`ListBucket`, `PutObject`, `DeleteObject` on bucket + prefix `/*`).
- Reads your **existing** website bucket (`data.aws_s3_bucket`) — it is **not** recreated here.

Does **not** create: CloudFront, RDS, custom domain ACM, VPC from scratch (uses default VPC if present).

## Prerequisites

1. [AWS CLI](https://docs.aws.amazon.com/cli/) configured (`aws sts get-caller-identity` works).
2. [Terraform](https://developer.hashicorp.com/terraform/install) `>= 1.5`.
3. An **EC2 key pair** name in the target region (**EC2 → Key pairs**).
4. **Default VPC** and a public subnet in that region (new accounts may need Default VPC recreated in VPC console).

## Commands

From this directory (`infra/terraform/`):

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: ec2_key_name, tighten admin_ssh_cidr if possible

terraform init
terraform plan
terraform apply
terraform output -raw aws_deploy_role_arn
terraform output -raw api_public_dns
```

## After `terraform apply`

### One-time EC2 bootstrap (SSH)

```bash
ssh -i /path/to/your-key.pem ec2-user@$(terraform output -raw api_public_dns)
sudo -iu ec2-user bash -lc 'cd ~/AtharvAyur && git clone https://github.com/riyay08/AtharvAyur.git .'
```

Use your repo URL / branch. For **private** repos use a [GitHub PAT](https://github.com/settings/tokens) in the clone URL (`https://TOKEN@github.com/...`) or deploy keys — do not leak tokens.

Configure **`~/AtharvAyur/backend/.env`** on the server (see [`../../docs/AWS_DEPLOYMENT.md`](../../docs/AWS_DEPLOYMENT.md)). At minimum align **`HOLISTICA_DB_PASSWORD`** and **`CORS_ORIGINS`** with your S3 website origin.

Start the stack:

```bash
cd ~/AtharvAyur/backend
docker compose -f docker-compose.aws.yml up -d --build
curl -sf http://127.0.0.1:8000/health && echo OK
```

### GitHub repository variables

Repo **Settings → Secrets and variables → Actions → Variables**:

| Variable | Value |
|---------|--------|
| `AWS_REGION` | Same as Terraform (e.g. `us-east-2`) |
| `AWS_DEPLOY_ROLE` | `terraform output -raw aws_deploy_role_arn` |
| `S3_BUCKET` | `terraform output -raw frontend_bucket` (or `atharvayur`) |
| `VITE_API_URL` | `http://<elastic-ip-or-dns>:8000` |
| `EC2_HOST` | Same public DNS/IP as terraform output (**after EIP associates**, use `terraform refresh` then output again) |

Leave **`CLOUDFRONT_FRONTEND_ID`** unset if you only use **S3 website** — the Deploy workflow skips invalidation when it is blank.

Secrets:

| Secret | Value |
|--------|--------|
| `EC2_SSH_KEY` | **Full** PEM private key matching the `.pem` used for SSH (workflow runs `deploy` backend job **only when** `EC2_HOST` is non-empty — set it once EC2 bootstrapped) |

Ensure **IAM → Identity providers**: GitHub OIDC thumbprint/list matches current GitHub docs if Terraform failed on OIDC duplication.

### OIDC duplicate error

If apply errors because the OIDC provider already exists:

1. Import it (replace account id):

   ```bash
   terraform import 'aws_iam_openid_connect_provider.github[0]' arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com
   ```

2. Or set `create_github_oidc_provider = false` in `terraform.tfvars`, **apply**, and confirm the IAM role trust policy references the existing provider ARN (same region/account).

### CloudFront invalidation IAM (optional)

If you later add **`CLOUDFRONT_FRONTEND_ID`**, attach an inline policy to the deploy role granting `cloudfront:CreateInvalidation` on your distribution ARN (extend Terraform or AWS console).

---

State file `terraform.tfstate` is ignored by `.gitignore` at repo root; keep it somewhere safe if you recreate infra.
