# Private: Environment & Secrets — ELI5 Guide (Do NOT commit)

IMPORTANT: This file contains instructions for handling secrets. Do NOT commit credentials, API keys, or secrets to the repository. Keep this file private and rotate any secrets if accidentally exposed.

This guide explains, in very simple terms, what environment variables and repository secrets are and how to set them for this project.

---

## 1) What is an "environment variable"?

- Imagine your app is a robot that needs a key to enter the castle (the database).
- An environment variable is a tiny note the robot reads when it wakes up that says where the key is and the secret password.
- We keep that note in a safe place (not in the robot's toolbox which is the git repo).

## 2) Why can't we put secrets in the code?

- If you put the secret note in the toolbox (the git repo), anyone who sees the toolbox (public or pushed repo) also sees the secret.
- That means bad people could get into your castle (database, cloud) and cause trouble.

## 3) Local development: using a `.env` file (safe for local only)

- Create a file named `.env` in the project root (same folder as `manage.py`).
- Put secret lines like this (example):

```env
# .env (DO NOT COMMIT)
DJANGO_SECRET_KEY=change-this-to-a-real-secret
DATABASE_URL=postgres://user:password@localhost:5432/cedrus_dev
SENTRY_DSN=__your_sentry_dsn_here__
ALLOWED_HOSTS=localhost,127.0.0.1
```

- Make sure `.env` is listed in `.gitignore` so it is never added to git. If your repo already has `.env` in `.gitignore`, you're good.

## 4) How to load `.env` in Django (what the code should do)

- Use a small helper package like `python-dotenv` or `django-environ`.
- Example (simple): in `cedrus/settings.py` near the top:

```python
from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')
```

- The code reads those notes when Django starts and never stores them in git.

## 5) GitHub: What are Repository Secrets and why we need them

- On GitHub, repository secrets are a safe place to store secrets for CI/CD.
- They are encrypted and only exposed to Actions at run-time.
- Use them to store `DJANGO_SECRET_KEY`, `DATABASE_URL` (production), `SENTRY_DSN`, and `CLOUD_*` keys.

## 6) How to add a Repository Secret on GitHub (manual steps)

1. Go to your repo on GitHub: `<https://github.com/<your-org>/<your-repo>>`
2. Click `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
3. Add a `Name` (e.g., `DJANGO_SECRET_KEY`) and the `Value` (the secret string).
4. Click `Add secret`.

Repeat for each secret you need.

## 7) How to use these secrets in GitHub Actions workflows

- In your workflow YAML, pass secrets to jobs like this:

```yaml
env:
  DJANGO_SECRET_KEY: ${{ secrets.DJANGO_SECRET_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}

steps:
  - name: Run tests
    run: |
      python -m pip install -r requirements.txt
      python manage.py test
```

- Secrets are not printed in workflow logs. If you accidentally `echo` them, GitHub will mask them, but don't rely on that.

## 8) Organization-level secrets (when you have multiple repos)

- GitHub allows org-level secrets that can be shared with selected repos.
- Use them for company-wide tokens and rotate carefully.

## 9) Using `gh` CLI to set secrets (optional)

- Install GitHub CLI: <https://cli.github.com/>
- Login: `gh auth login`
- Set repo secret using:

```bash
gh secret set DJANGO_SECRET_KEY -b"my-secret-value" --repo my-org/00_cedrus
```

## 10) What about environment variables on production servers?

- On a server (e.g., a VM or container), set env vars in the service config or the container runtime, not in the repo.
- Example for systemd (on server):

```ini
# /etc/systemd/system/cedrus.service
[Service]
Environment=DJANGO_SECRET_KEY=supersecretvalue
Environment=DATABASE_URL=postgres://user:pass@db:5432/prod_db
```

- For Docker, pass envs in `docker-compose.yml` or use an env file referenced by `docker-compose` but keep that file out of git.

## 11) Rotating and revoking secrets

- If a secret may have been exposed, rotate it immediately: create a new secret value, update the service and GitHub secret, then revoke the old one.
- Example: rotate DB password, update `DATABASE_URL` secret, restart services.

## 12) What to do if you accidentally commit a secret

1. Remove the secret from history: `git rm --cached path/to/file` and commit removal.
2. Purge history if necessary (dangerous): `git filter-branch` or `git filter-repo` to remove earlier commits.
3. **Immediately rotate** the secret (assume compromised).

## 13) Minimal `.env.example` to include in repo (safe to commit)

- Create a file `.env.example` with placeholder keys (no secrets):

```env
# .env.example (safe to commit)
DJANGO_SECRET_KEY=replace-with-secret
DATABASE_URL=postgres://user:password@host:port/dbname
SENTRY_DSN=replace-with-dsn
ALLOWED_HOSTS=localhost,127.0.0.1
```

This helps new developers know what to set, without exposing secrets.

## 14) Quick Checklist (Do this now)

- [ ] Create `.env` locally and add real secrets to it (do not commit).
- [ ] Ensure `.gitignore` contains `.env`.
- [ ] Add repository secrets in GitHub for production values.
- [ ] Reference `secrets.*` in GitHub Actions workflows via `${{ secrets.NAME }}`.
- [ ] Rotate any secrets that may have been committed accidentally.

## 15) Helpful Commands

```bash
# Mask a file locally (do not commit):
echo '.env' >> .gitignore

# Remove an accidentally committed file from next commit
git rm --cached .env
git commit -m "Remove .env from repository"

# Set a repo secret via gh CLI (example)
gh secret set DJANGO_SECRET_KEY -b"$(python -c 'from secrets import token_urlsafe; print(token_urlsafe(50))')" --repo my-org/00_cedrus
```

---

If you want, I can:

- Create an example `.env.example` file in the repo (safe to commit).
- Scaffold a minimal GitHub Actions workflow that reads from secrets and runs tests (will create PR if you want).

*File created: `docs/PRIVATE_ENV_SECRETS_ELI5.md` — DO NOT COMMIT this file.*
