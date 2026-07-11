# GOLD Px Backend

Production backend for **GOLD Px (Ghousia Off Light Decorations & Pixels)** — Wedding Lighting,
Event Decoration, Pixel LED Installations, Stage & Architectural Lighting, Smart RGB Pixel Systems.

This build focuses on a fully working **foundation + Booking system end-to-end**:
Authentication & Roles → Bookings → Attachments → Quotations → Approval Workflow →
Invoices & Payments → Timeline → Notifications (WhatsApp deep-links + Email) → Dashboard analytics.

Other PRD modules (Portfolio, Lighting Configurator, Testimonials, Blog/CMS, full Push
notifications) are scaffolded architecturally but not yet built — see **Roadmap** below.

---

## Tech Stack

- **FastAPI** (Python 3.12) — async-ready REST API
- **PostgreSQL** + **SQLAlchemy 2.0** (typed models) + **Alembic** (migrations)
- **JWT** access/refresh tokens, role-based permissions
- **Redis** + **Celery** — background tasks (currently: async email sending)
- **Docker / Docker Compose / NGINX** — production deployment
- Local file storage today; **Cloudinary/S3 swap-in ready** (one file to change, see below)

---

## Quick Start (Docker)

```bash
cp .env.example .env
# edit .env: set a real SECRET_KEY at minimum

docker compose up --build -d

# create tables (dev quick-start; use Alembic for real migrations, see below)
docker compose exec api python scripts/init_db.py

# seed a super admin + manager + staff + sample bookings
docker compose exec api python scripts/seed_data.py
```

Then open:
- API docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Via NGINX: http://localhost/docs

Seeded logins (from `scripts/seed_data.py`):
| Role | Email | Password |
|---|---|---|
| Super Admin | admin@goldpx.com | ChangeMe123! |
| Manager | manager@goldpx.com | Password123 |
| Staff | staff@goldpx.com | Password123 |

---

## Local Development (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# make sure Postgres + Redis are running locally, then:
cp .env.example .env   # set POSTGRES_HOST=localhost, REDIS_HOST=localhost

python scripts/init_db.py
python scripts/seed_data.py

uvicorn app.main:app --reload
```

Run the Celery worker in a second terminal:
```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

---

## Database Migrations (Alembic)

`scripts/init_db.py` is a fast way to create tables for local testing. For real environments,
use Alembic so schema changes are tracked and reversible:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

`alembic/env.py` is already wired to `app.core.config.settings` and imports every model via
`app.models`, so autogenerate sees the full schema (users, bookings, quotations, invoices,
payments, attachments, timeline events, notifications, audit logs, OTP/reset/refresh tokens).

---

## Architecture

```
app/
  core/           config.py (env settings), security.py (JWT/hashing), celery_app.py
  db/             base_class.py (declarative base w/ id+timestamps), session.py (engine/session)
  models/         SQLAlchemy models: user, auth_tokens, booking, quotation, invoice, notification
  schemas/        Pydantic request/response models
  api/
    deps.py       get_current_user, require_min_role(), require_roles()
    v1/
      api.py      router aggregator
      endpoints/  auth, users, bookings, attachments, quotations, invoices, dashboard, notifications
  services/       business logic: booking_service, storage_service, whatsapp_service,
                  email_service, notification_service
  tasks/          Celery background tasks (async email)
  utils/          reference.py (human-readable ref no generator)
scripts/          init_db.py, seed_data.py
alembic/          migrations
nginx/            reverse proxy config
docker-compose.yml, Dockerfile, .env.example
```

### Roles (low → high)
`guest → customer → staff → manager → admin → super_admin`

Enforced via two dependency helpers in `app/api/deps.py`:
- `require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)` — exact role match
- `require_min_role(UserRole.STAFF)` — role rank ≥ given role

### Booking lifecycle
```
NEW → UNDER_REVIEW → QUOTATION_SENT → APPROVED → IN_PROGRESS → COMPLETED
                                    ↘ REJECTED ↗
              (CANCELLED reachable from most states)
```
Transitions are validated server-side in `app/services/booking_service.py`
(`VALID_TRANSITIONS`) — invalid jumps return `400`. Every status/payment/quotation/invoice
change writes a `BookingTimelineEvent`, which powers the booking Timeline in the UI.

### Notifications today (no paid API keys yet)
- **WhatsApp**: no Business API key configured. Instead of auto-sending, the backend generates
  a pre-filled **wa.me deep link** (`https://wa.me/<customer_number>?text=...`) every time a
  booking is created, a quotation is sent, or a booking is approved. Staff open
  `GET /api/v1/notifications/` in the dashboard, click the link to open WhatsApp with the
  message pre-typed, hit send themselves, then `PATCH /notifications/{id}/mark-sent`.
  The company's own WhatsApp is `wa.me/923145355656` (`WHATSAPP_BUSINESS_NUMBER` in `.env`).
- **Email**: sent via SMTP if `SMTP_HOST/USER/PASSWORD` are set in `.env`; otherwise the
  message is logged instead of silently failing, so nothing breaks in dev.
- **SMS**: not wired to a provider yet (`SMS_PROVIDER_ENABLED=false`) — OTP codes are logged
  server-side in the meantime so you can still test OTP login end-to-end.
- **Push**: not implemented yet (see Roadmap).

### File uploads / swap-in path for Cloudinary & S3
`app/services/storage_service.py` is the single seam. Today `STORAGE_BACKEND=local` saves to
`./uploads` (served via NGINX `/static/`). To switch to Cloudinary or S3 later: fill in the
credentials in `.env`, set `STORAGE_BACKEND=cloudinary` (or `s3`), and uncomment the ~4 lines
already sketched in that file. No endpoint code needs to change.

---

## Key API Endpoints

All prefixed with `/api/v1`. Full interactive reference at `/docs`.

**Auth**
`POST /auth/signup` · `/auth/login` · `/auth/google` · `/auth/otp/request` · `/auth/otp/verify`
`/auth/forgot-password` · `/auth/reset-password` · `/auth/verify-email` · `/auth/refresh` · `GET /auth/me`

**Users** (staff+)
`GET /users/` (search/filter/paginate) · `GET /users/{id}` · `PATCH /users/{id}/role` (admin+) · `PATCH /users/{id}/deactivate`

**Bookings**
`POST /bookings/` (public/guest) · `GET /bookings/` (staff+, filter/search/sort/paginate)
`GET /bookings/my` (customer's own) · `GET /bookings/{id}` · `PATCH /bookings/{id}`
`PATCH /bookings/{id}/status` (workflow-validated) · `PATCH /bookings/{id}/payment-status`
`DELETE /bookings/{id}` (cancel, manager+)

**Attachments**
`POST /bookings/{id}/attachments` (multipart upload) · `DELETE /bookings/{id}/attachments/{attachment_id}`

**Quotations**
`POST /bookings/{id}/quotations` (staff+, line items → subtotal/discount/tax/total)
`GET /bookings/{id}/quotations` · `POST /bookings/{id}/quotations/{qid}/respond` (customer accept/reject)

**Invoices & Payments**
`POST /bookings/{id}/invoices` · `GET /bookings/{id}/invoices`
`POST /bookings/{id}/invoices/{invoice_id}/payments` (auto-updates invoice + booking payment status)

**Dashboard** (manager+)
`GET /dashboard/summary` (revenue, upcoming events, pending quotations/payments, status breakdown)
`GET /dashboard/revenue-chart?days=30`

**Notifications** (staff+)
`GET /notifications/` · `PATCH /notifications/{id}/mark-sent`

---

## Security notes

- Passwords hashed with bcrypt (`passlib`)
- JWT access (30 min default) + refresh (30 days) tokens, refresh tokens stored hashed and
  revocable (`RefreshToken` table)
- All mutating booking endpoints require authentication; role checks via `require_min_role`
- Guests can only create bookings (`POST /bookings/`) — read/list/update all require an account
- Set a real `SECRET_KEY` before deploying; never commit `.env`
- Add a rate-limiting layer (e.g. `slowapi` or NGINX `limit_req`) in front of `/auth/*` before
  production traffic — not yet wired in this build

---

## Roadmap (from the full PRD, not yet built)

- Portfolio module (categories, gallery images/videos, before/after, featured, search/filters)
- Lighting Configurator API (RGB/DMX scenes, pixel/brightness config, animation library, JSON export/import)
- Testimonials (CRUD, ratings, photo/video reviews, approval, featured)
- CMS (Hero/Services/About/FAQ/Blog/Footer/SEO)
- Real WhatsApp Business API / SMS provider integration (currently deep-links + logging)
- Push notifications
- Audit log endpoints (model already exists: `AuditLog`)
- Rate limiting middleware, CSRF hardening for cookie-based flows, CI/CD pipeline
