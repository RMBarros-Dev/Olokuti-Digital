# Operations & Production Runbook — Olokuti Digital

## 1. Pre-Deployment Checklist

Before shipping any code or schema change:

1. Ensure CI passes completely:
   - `python -m ruff check .`
   - `python -m ruff format --check .`
   - `python -m pytest --cov=apps --cov=config --cov-fail-under=90`
   - `python manage.py makemigrations --check --dry-run --settings=config.settings.test`
   - `python manage.py check --deploy --fail-level WARNING` (with production env vars set)
2. Verify `.env` / platform secret variables are populated securely and never committed.
3. Confirm database backup snapshot in Supabase before running any pending Django migrations.

## 2. Supabase PostgreSQL & Connection Pooling

- For PgBouncer transaction-mode pooler URLs (port `6543` or `?pgbouncer=true`), `config.settings.base.database_from_url()` automatically disables persistent Django connections (`CONN_MAX_AGE=0`) and server-side cursors (`DISABLE_SERVER_SIDE_CURSORS=True`).
- Always enforce `sslmode=require` on external PostgreSQL connections.
- For multi-worker Gunicorn deployments, configure either `REDIS_URL` or `DJANGO_CACHE_DIR` so rate-limit counters share state cleanly across worker processes.

## 3. Database Backup & Recovery

1. **Logical Backup (`pg_dump`):**
   Use a read/backup role with TLS and store dumps in encrypted off-site storage:
   ```bash
   pg_dump --format=custom --no-owner --no-privileges --dbname="$DATABASE_URL" -f olokuti-backup.dump
   ```
2. **Verification:** Regularly test `pg_restore` into an isolated staging database to verify dump integrity and schema compatibility.

## 4. Migration Safety & Rollback Protocol

- Always inspect pending SQL locally via `python manage.py sqlmigrate <app> <migration>` before applying in production.
- **Pre-migration:** Take a manual snapshot in Supabase Dashboard.
- **Apply:** `python manage.py migrate --noinput`.
- **Rollback:** If an application release introduces a fault:
  1. Roll back the application deployment artifact (previous image/commit on Railway/Render).
  2. Only reverse migrations if needed and safe for non-destructive schema changes (`python manage.py migrate <app> <previous_migration>`), or restore from the pre-deploy PostgreSQL snapshot for irreversible data changes.

## 5. High Contrast Accessibility Verification

- Global high-contrast toggle (`[data-contrast-toggle]`) persists across page reloads and tabs via `localStorage` (`olokuti_high_contrast`), loads cleanly with CSP `nonce` without FOUC, updates `aria-pressed`, and announces state transitions via `#a11y-contrast-status`.
