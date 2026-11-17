# Architecture Overview — Olokuti Digital

Olokuti Digital is a modular monolithic Django 5.2 application designed for sustainable commerce operations, catalog management, inventory control, operational task coordination, and auditability.

## Layering & Domain Boundaries

Each Django app under `apps/` separates responsibilities cleanly:

| App / Module | Responsibility | Key Patterns |
| --- | --- | --- |
| `apps.accounts` | Authentication, fail-closed public registration, RBAC roles, dashboard KPIs, user admin | Rate limiting (`apps/accounts/ratelimit.py`), `ActiveUserRequiredMiddleware`, session invalidation |
| `apps.catalog` | Categories, Products (`sku`, `barcode`, `price`, `currency`, `attributes`, `is_active`), `ProductTranslation` | Partial unique SKU constraint, non-negative price check, localized selectors |
| `apps.inventory` | `StockLocation`, `StockItem`, immutable `StockMovement` ledger | Transactional `select_for_update()` balance locking in `apps/inventory/services.py` |
| `apps.operations` | `OperationalTask` (`category`, `status`, `priority`), `TaskComment` | HTMX partial table updates, task history via `AuditLog`, category filtering |
| `apps.reports` | Aggregations for products, tasks, collaborator productivity, and inventory | ORM aggregations, formula-safe CSV streaming (`config/csv.py`), pure-Python PDF (`config/pdf.py`) |
| `apps.audit` | Immutable `AuditLog` model, `record_event()`, `AuditedAdminMixin` | Write-protected admin, standardized JSON metadata details |

## Request & Security Pipeline

1. **`SecurityHeadersMiddleware`** generates a per-request cryptographic CSP nonce (`csp_nonce`), sets strict `script-src 'self' 'nonce-...'` without `'unsafe-inline'`, configures `Permissions-Policy`, and enforces referrer/framing policies.
2. **`ActiveUserRequiredMiddleware`** invalidates and logs out deactivated accounts immediately across active sessions.
3. **`config/settings/validators.py`** validates production startup configuration (`DJANGO_SECRET_KEY`, PostgreSQL `DATABASE_URL`, explicit `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, non-console SMTP backend, and HSTS minimum duration).
4. **Supabase Pooler Compatibility:** `database_from_url()` automatically sets `CONN_MAX_AGE=0` and `DISABLE_SERVER_SIDE_CURSORS=True` and strips `pgbouncer` from psycopg `OPTIONS` when port `6543` or `pgbouncer=true` is present.
