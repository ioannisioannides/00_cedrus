# GitHub Secrets Configuration
## Required for CI/CD Pipeline and Deployments

**Document Owner:** Dr. Thomas Berg (DevOps Architect)  
**Security Review:** Col. Marcus Stone (Security Agent)  
**Last Updated:** November 21, 2025

---

## 📋 Overview

This document lists all GitHub Secrets required for the Cedrus CI/CD pipeline and production deployments. These secrets must be configured in your GitHub repository settings before deploying to production.

**Navigation:** Repository → Settings → Secrets and variables → Actions → New repository secret

---

## 🔑 Required Secrets

### 1. Django Application Secrets

#### `DJANGO_SECRET_KEY` (CRITICAL)
- **Purpose:** Django cryptographic signing key for production
- **Required For:** Production deployment, security features
- **How to Generate:**
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```
- **Format:** 50-character random string
- **Example:** `django-insecure-abc123...xyz789` (but NEVER use example keys!)
- **Security:** NEVER commit to git, NEVER share publicly

#### `DJANGO_ALLOWED_HOSTS`
- **Purpose:** Comma-separated list of allowed hostnames
- **Required For:** Production Django deployment checks
- **Format:** `domain1.com,domain2.com,subdomain.domain.com`
- **Example:** `cedrus.yourdomain.com,www.cedrus.yourdomain.com`
- **Note:** Include both apex domain and www subdomain if applicable

#### `DJANGO_CSRF_TRUSTED_ORIGINS`
- **Purpose:** Comma-separated list of trusted CSRF origins (HTTPS URLs)
- **Required For:** CSRF protection with HTTPS
- **Format:** `https://domain1.com,https://domain2.com`
- **Example:** `https://cedrus.yourdomain.com,https://www.cedrus.yourdomain.com`

---

### 2. Database Secrets

#### `DB_NAME`
- **Purpose:** PostgreSQL database name
- **Default:** `cedrus_production`
- **Example:** `cedrus_prod`

#### `DB_USER`
- **Purpose:** PostgreSQL username
- **Default:** `cedrus`
- **Example:** `cedrus_app`

#### `DB_PASSWORD` (CRITICAL)
- **Purpose:** PostgreSQL password
- **Required For:** Database connection
- **How to Generate:**
  ```bash
  openssl rand -base64 32
  ```
- **Security:** Use strong passwords (32+ characters, mixed case, numbers, symbols)

#### `DB_HOST`
- **Purpose:** PostgreSQL server hostname or IP
- **Default:** `localhost` (development)
- **Example:** `db.yourdomain.com` or `10.0.1.50`

#### `DB_PORT`
- **Purpose:** PostgreSQL port
- **Default:** `5432`
- **Example:** `5432` (standard PostgreSQL port)

#### `DATABASE_URL` (Alternative)
- **Purpose:** Single connection string for all database config
- **Format:** `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`
- **Example:** `postgresql://cedrus:strongpass@db.example.com:5432/cedrus_prod`
- **Note:** Can be used instead of individual DB_* variables

---

### 3. Deployment Secrets

#### `SSH_PRIVATE_KEY` (if using SSH deployment)
- **Purpose:** SSH key for server access
- **Required For:** Remote deployment to servers
- **How to Generate:**
  ```bash
  ssh-keygen -t ed25519 -C "github-actions@cedrus-deploy" -f cedrus_deploy_key
  ```
- **Format:** Full private key including headers
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtz...
  -----END OPENSSH PRIVATE KEY-----
  ```
- **Security:** Add public key to server's `~/.ssh/authorized_keys`

#### `PRODUCTION_HOST`
- **Purpose:** Production server IP or hostname
- **Required For:** Deployment scripts
- **Example:** `production.cedrus.yourdomain.com` or `203.0.113.50`

#### `STAGING_HOST`
- **Purpose:** Staging server IP or hostname
- **Required For:** Staging deployment
- **Example:** `staging.cedrus.yourdomain.com`

---

### 4. Optional Monitoring & Notification Secrets

#### `SLACK_WEBHOOK_URL`
- **Purpose:** Slack webhook for deployment notifications
- **Required For:** Slack integration (optional)
- **How to Get:** Slack → Apps → Incoming Webhooks
- **Format:** `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`

#### `DISCORD_WEBHOOK_URL`
- **Purpose:** Discord webhook for notifications
- **Required For:** Discord integration (optional)
- **Format:** `https://discord.com/api/webhooks/123456789/abcdef...`

#### `SENTRY_DSN`
- **Purpose:** Sentry error tracking
- **Required For:** Sentry integration (optional)
- **How to Get:** Sentry.io → Project Settings → Client Keys (DSN)
- **Format:** `https://abc123@o123.ingest.sentry.io/456`

#### `CODECOV_TOKEN`
- **Purpose:** Codecov test coverage reporting
- **Required For:** Codecov integration (optional)
- **How to Get:** Codecov.io → Repository Settings → Upload Token

---

### 5. Security Scanning Secrets

#### `SNYK_TOKEN`
- **Purpose:** Snyk vulnerability scanning
- **Required For:** Snyk security checks (optional)
- **How to Get:** Snyk.io → Account Settings → API Token
- **Format:** UUID string

#### `GITHUB_TOKEN`
- **Purpose:** GitHub API access (automatically provided)
- **Required For:** GitHub Actions (automatic)
- **Note:** No configuration needed, provided by GitHub

---

## 🔧 Configuration Steps

### Step 1: Add Secrets to GitHub

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter **Name** and **Value** for each secret
5. Click **Add secret**

### Step 2: Verify Secrets Are Set

Run this workflow manually to verify secrets (without exposing values):

```yaml
name: Verify Secrets
on: workflow_dispatch

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
    - name: Check secrets
      run: |
        echo "DJANGO_SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY != '' && '✅ Set' || '❌ Missing' }}"
        echo "DB_PASSWORD: ${{ secrets.DB_PASSWORD != '' && '✅ Set' || '❌ Missing' }}"
        # Add more checks as needed
```

### Step 3: Update Environment Variables

For production deployment, ensure your `.env` file (or environment configuration) includes:

```bash
# Copy .env.example to .env and fill in values
DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY}"
DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS}"
DEBUG=False
DATABASE_URL="${DATABASE_URL}"
# ... etc
```

---

## 🔐 Security Best Practices

### ✅ DO:
- ✅ Use strong, randomly generated passwords
- ✅ Rotate secrets regularly (every 90 days)
- ✅ Use separate secrets for staging and production
- ✅ Limit secret access to necessary workflows only
- ✅ Use GitHub organization secrets for shared resources
- ✅ Enable secret scanning on your repository
- ✅ Review secret access logs periodically

### ❌ DON'T:
- ❌ NEVER commit secrets to git
- ❌ NEVER share secrets in chat/email/issues
- ❌ NEVER use weak or default passwords
- ❌ NEVER reuse secrets across environments
- ❌ NEVER log secret values in workflows
- ❌ NEVER use secrets in pull requests from forks

---

## 🚨 Secret Leak Response

If a secret is accidentally exposed:

1. **Immediately revoke/rotate the secret**
2. **Remove from GitHub history** (if committed):
   ```bash
   # Use BFG Repo-Cleaner or git-filter-repo
   git filter-repo --path-glob '*.env' --invert-paths
   ```
3. **Update GitHub secret** with new value
4. **Redeploy affected services** with new secrets
5. **Audit access logs** for unauthorized usage
6. **Review security practices** to prevent recurrence

---

## 📊 Secrets Checklist

Before deploying to production, verify all required secrets are configured:

- [ ] `DJANGO_SECRET_KEY` - Generated and set
- [ ] `DJANGO_ALLOWED_HOSTS` - Production domains configured
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS` - HTTPS origins configured
- [ ] `DB_PASSWORD` - Strong password set
- [ ] `DB_NAME`, `DB_USER`, `DB_HOST` - Database config complete
- [ ] `SSH_PRIVATE_KEY` - Deployment key configured (if applicable)
- [ ] `PRODUCTION_HOST` - Server address set (if applicable)
- [ ] Optional: Monitoring/notification secrets configured

---

## 📖 Additional Resources

- [GitHub Encrypted Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)

---

## 🆘 Support

If you need assistance configuring secrets:

1. **Development Environment:** Use `.env.example` as template
2. **CI/CD Issues:** Check GitHub Actions logs (secrets are masked)
3. **Security Concerns:** Contact security team immediately
4. **Production Deployment:** Follow deployment runbook

---

**Remember:** Secrets are sensitive! Handle with care and follow security best practices.
