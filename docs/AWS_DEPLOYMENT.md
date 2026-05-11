# Deploy frontend and backend to AWS

This repository is already wired for a **practical split**:

| Piece | Where it runs | How it deploys |
|--------|----------------|----------------|
| **Frontend** (Vite static build) | **S3** (optionally **CloudFront**) | GitHub Actions **`frontend`** job — uploads **`dist/`** to S3; CloudFront invalidation runs **only** if **`CLOUDFRONT_FRONTEND_ID`** is set (omit for S3 static website hosting). |
| **Backend** (FastAPI + Postgres) | **EC2** (Docker) | Job **`backend`** runs **only** if **`EC2_HOST`** is set — SSH, `git pull`, `docker compose -f docker-compose.aws.yml`. |

### Fast path: Terraform bootstrap

To provision **EC2 + Elastic IP + GitHub Actions OIDC role scoped to your S3 bucket**, use Terraform in **[`infra/terraform/README.md`](../infra/terraform/README.md)** on your workstation (needs **your** AWS credentials).

You cannot operate your AWS/GitHub credentials from Cursor. Follow Terraform + the checklist once; afterward **every push to `main`** can deploy (frontend anytime; backend once **`EC2_HOST`** / **`EC2_SSH_KEY`** exist).

---

## 1. What you need in AWS

1. **EC2 instance** (e.g. Amazon Linux 2023 or Ubuntu 22.04), **public IP or Elastic IP**, in a **VPC** with a security group that allows:
   - **TCP 22** — SSH from *somewhere* GitHub Actions can reach.  
     GitHub-hosted runners use [changing IP ranges](https://api.github.com/meta) (`actions` in the JSON). For a first setup, many teams temporarily allow `0.0.0.0/0` on port 22 **only** with key-based auth, then tighten (self-hosted runner, SSM, or IP allowlist).
   - **TCP 80 / 443** (recommended) — public **HTTPS** for the API (see section 5). Opening **8000** to the world works for a quick smoke test but is poor for production and breaks **HTTPS frontend → HTTP API** (mixed content).

2. **S3 bucket** — holds the built static files (`dist/`).

3. **CloudFront distribution** — origin = that S3 bucket (use OAC / OAI). Point your **frontend domain** (optional) at CloudFront.

4. **IAM role for GitHub Actions (OIDC)** — trust policy allows `sts:AssumeRoleWithWebIdentity` from GitHub for **this** repo only. Attach a policy that allows at least:
   - `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket` on the deploy bucket (and prefix `assets/` if you scope narrowly).
   - `cloudfront:CreateInvalidation` on your distribution ARN.

5. **DNS (optional but typical)** — e.g. Route 53: `app.example.com` → CloudFront, `api.example.com` → EC2 or ALB.

---

## 2. Prepare the EC2 host (one time)

On the instance (as the user that will own the deploy path, often `ec2-user` or `ubuntu`):

```bash
# Docker + Compose plugin (Amazon Linux 2023 example; adjust for Ubuntu)
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
# Log out and back in so docker group applies.

sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
```

Clone the app **to the path the workflow expects** (default: `~/AtharvAyur`):

```bash
mkdir -p ~/AtharvAyur && cd ~/AtharvAyur
git clone https://github.com/riyay08/AtharvAyur.git .
# or: git clone git@github.com:riyay08/AtharvAyur.git .
cd backend
cp .env.example .env
```

Edit **`backend/.env`** on the server (never commit real secrets). For [docker-compose.aws.yml](../backend/docker-compose.aws.yml), **`DATABASE_URL` in `.env` is overridden** by Compose to use the `db` service; still set a strong **`HOLISTICA_DB_PASSWORD`** in `.env` (and the same value is used in the compose interpolation for Postgres and the API).

Minimum to think about:

- `HOLISTICA_DB_PASSWORD`, `JWT_SECRET_KEY`
- `LLM_PROVIDER`, `GROQ_API_KEY` and/or `GEMINI_API_KEY`
- `CORS_ORIGINS` — must include your **CloudFront URL** (and custom domain if any), e.g. `https://d1234567890.cloudfront.net`
- `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN` — must match the **browser origin** users see (your CloudFront / custom domain), not `localhost`
- `GOOGLE_CLIENT_ID` if you use Google sign-in

First deploy on the box:

```bash
cd ~/AtharvAyur/backend
docker compose -f docker-compose.aws.yml up -d --build
curl -fsS http://127.0.0.1:8000/health
```

---

## 3. GitHub repository configuration

In the repo: **Settings → Secrets and variables → Actions**.

### Secrets

| Name | Used by |
|------|---------|
| `EC2_SSH_KEY` | Backend job — **private** half of the SSH key whose public key is in `~/.ssh/authorized_keys` on the EC2 user |

### Variables (repository **Variables**, not secrets)

| Name | Example | Purpose |
|------|---------|---------|
| `AWS_REGION` | `us-east-1` | Region for S3 / CloudFront CLI |
| `AWS_DEPLOY_ROLE` | `arn:aws:iam::123456789012:role/github-deploy-atharvayur` | IAM role ARN for OIDC |
| `S3_BUCKET` | `atharvayur-frontend-prod` | Frontend bucket |
| `CLOUDFRONT_FRONTEND_ID` | `E1234567890ABC` | Distribution ID for invalidation |
| `VITE_API_URL` | `https://api.example.com` | **Public base URL of the API** (no trailing slash). Baked in at **build** time. |
| `EC2_HOST` | `ec2-1-2-3-4.compute-1.amazonaws.com` or Elastic IP DNS | SSH target |
| `EC2_USER` | `ec2-user` or `ubuntu` | SSH user |

**OIDC:** In IAM, create the role `AWS_DEPLOY_ROLE` with a trust policy that restricts `sub` to your repo, e.g. `repo:riyay08/AtharvAyur:ref:refs/heads/main` (and `workflow_dispatch` if you use that). Attach the S3 + CloudFront policy described above.

---

## 4. Frontend build and API URL

The workflow runs `npm run build` with `VITE_API_URL` set from **`vars.VITE_API_URL`**. The SPA then calls that host directly for API requests (see `src/services/apiClient.js`).

So:

- After you put HTTPS in front of the API, set `VITE_API_URL` to that **https** URL and redeploy (push to `main` or **Run workflow**).
- **`CORS_ORIGINS`** on the backend must list the **exact** frontend origin (CloudFront `https://...` or custom domain).

---

## 5. HTTPS for the API (strongly recommended)

CloudFront serves the site over **HTTPS**. Browsers block **mixed content** if the SPA calls **`http://`** on another host.

Pick one:

- **Reverse proxy on EC2** (Caddy or nginx) on **443** → proxy to `http://127.0.0.1:8000`, with Let’s Encrypt (e.g. Certbot) for `api.example.com`.
- **Application Load Balancer** in front of the instance (or in front of a future ECS service) with ACM certificate and target group to port 8000.

Until HTTPS is in place, use a **temporary** setup only: same-protocol testing or a tunnel—not a public production app.

---

## 6. Run the pipeline

- **Automatic:** push to **`main`** (workflow triggers on `push` to `main` and on `workflow_dispatch`).
- **Manual:** Actions tab → **Deploy** → **Run workflow**.

Fix any failing step logs (tests, AWS permissions, SSH, Docker health).

---

## 7. Optional improvements

- Replace SSH-from-GitHub with **SSM Run Command**, **CodeDeploy**, or **ECS/Fargate** + ECR for stricter, keyless deploys.
- Add **WAF** on CloudFront, **RDS** instead of Postgres-in-Docker for durability, and **Secrets Manager** for env secrets.

---

## 8. Example: your S3 static website frontend

If the browser loads the app from the **S3 website endpoint** (HTTP), for example:

**`http://atharvayur.s3-website.us-east-2.amazonaws.com`**

then on the **API** host set **`CORS_ORIGINS`** to include that origin **exactly** (scheme + host, no trailing path; add more origins separated by commas if you also use localhost for dev):

```env
CORS_ORIGINS=http://atharvayur.s3-website.us-east-2.amazonaws.com,http://localhost:5173,http://127.0.0.1:5173
```

Rebuild / restart the API after changing `CORS_ORIGINS`.

### GitHub Actions `VITE_API_URL`

The frontend build must know the **API base URL** (not the S3 URL). In repo **Settings → Variables → Actions**, set `VITE_API_URL` to whatever users’ browsers will call, for example:

- `http://YOUR_EC2_PUBLIC_DNS:8000` (only if port **8000** is open in the security group and you accept HTTP), or  
- `https://api.yourdomain.com` once you terminate TLS in front of the API.

After changing `VITE_API_URL`, run the **Deploy** workflow (or push to `main`) so a new `dist/` is built and uploaded.

### WebAuthn (passkeys) on `*.amazonaws.com`

Passkeys rely on a **registrable domain** you control. The default **S3 website hostname** is usually **not suitable** for production WebAuthn: browsers and RP ID rules may block or behave inconsistently compared to a **custom domain** in front of **CloudFront** (or another CDN) with `WEBAUTHN_RP_ID` / `WEBAUTHN_ORIGIN` matching that site. Email / password / phone OTP / Google sign-in can still work; plan a custom domain before relying on passkeys in production.

---

## Quick reference — files

| File | Role |
|------|------|
| [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) | CI/CD |
| [`backend/docker-compose.aws.yml`](../backend/docker-compose.aws.yml) | API + Postgres on EC2 |
| [`backend/Dockerfile`](../backend/Dockerfile) | API image |
