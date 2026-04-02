# Finance Dashboard Backend API

A clean FastAPI backend for a finance dashboard application with JWT authentication, centralized RBAC, transaction management, and database-level dashboard aggregations.

## Tech Stack

- FastAPI
- SQLAlchemy ORM
- PostgreSQL (Supabase-ready via `DATABASE_URL`)
- Pydantic
- Custom JWT implementation

## Features

- User registration and login
- Seeded first admin via `.env`
- Centralized RBAC for `viewer`, `analyst`, and `admin`
- Transaction CRUD with soft delete
- Filtering, search, and pagination for transaction listings
- User-scoped dashboard summary, category totals, trends, and recent transactions
- Standardized success responses: `{ "success": true, "data": ... }`
- Basic auth rate limiting for `/auth/register` and `/auth/login`
- Swagger docs at `/docs`
- Minimal automated tests for auth and transaction flows

## Project Structure

```text
app/
  core/           # settings, security, responses, exception handlers
  db/             # SQLAlchemy base, engine, session management
  dependencies/   # auth and RBAC dependencies
  models/         # database models and enums
  routes/         # API endpoints
  schemas/        # request and response validation
  services/       # business logic
  main.py         # FastAPI app entrypoint
tests/            # auth and transaction flow tests
```

## Environment Variables

Copy `.env.example` to `.env` and update the values:

```env
DATABASE_URL=postgresql+psycopg://postgres:yourpassword@db.your-project.supabase.co:5432/postgres
JWT_SECRET=replace-with-a-long-random-secret
JWT_EXPIRE_MINUTES=60
AUTH_RATE_LIMIT_REQUESTS=5
AUTH_RATE_LIMIT_WINDOW_SECONDS=60
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=AdminPass123
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for Swagger UI.

## Postman Quick Testing

For faster endpoint testing, import the Postman files in the `postman/` folder:

- `postman/finance-dashboard-api.postman_collection.json`
- `postman/finance-dashboard-role-tests.postman_collection.json`
- `postman/finance-dashboard-local.postman_environment.json`

After importing, select the local environment and run `Login Admin` or `Login Viewer` first so `{{token}}` is populated for protected API calls.

## Running Tests

```bash
pytest
```

## Docker Deployment

Build and run with Docker:

```bash
docker build -t fincial-dashboard-api:latest .
docker run -d --name fincial-dashboard-api -p 8000:8000 --env-file .env fincial-dashboard-api:latest
```

Published Docker image:

`docker.io/farissait7/financial-dashboard-api:latest`
`farissait7/financial-dashboard-api:latest`

Pull and run the published image:

```bash
docker pull farissait7/financial-dashboard-api:latest
docker run -d --name fincial-dashboard-api -p 8000:8000 --env-file .env farissait7/financial-dashboard-api:latest
```

Or run with Docker Compose:

```bash
docker compose up --build -d
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) after the container starts.

## Live Deployment

Railway URL:

`https://financial-dashboard-api-production-e7e7.up.railway.app`

## Make It Publicly Accessible

Option 1 (production): deploy this Dockerized app to a public cloud service like Railway, Render, Fly.io, AWS, or a VPS.  
Option 2 (quick demo): run locally and expose it using a tunnel tool like `cloudflared` or `ngrok`.

Quick tunnel example with Cloudflare:

```bash
cloudflared tunnel --url http://localhost:8000
```

It gives a public HTTPS URL you can share for testing.

## Role-By-Role Postman Testing

Use the `finance-dashboard-role-tests` collection folders:

- `Role - Admin`
- `Role - Analyst`
- `Role - Viewer`

Run each folder separately in Postman to test permissions role by role.

## API Overview

### Authentication

- `POST /auth/register`
- `POST /auth/login`

Both auth endpoints are rate-limited per client IP using:

- `AUTH_RATE_LIMIT_REQUESTS` (default `5`)
- `AUTH_RATE_LIMIT_WINDOW_SECONDS` (default `60`)

### Users

- `GET /users`
- `PATCH /users/{id}/role`
- `PATCH /users/{id}/status`

### Transactions

- `POST /transactions`
- `GET /transactions`
- `GET /transactions/{id}`
- `PUT /transactions/{id}`
- `DELETE /transactions/{id}`
- `PATCH /transactions/{id}/restore`

Supported transaction list query params:

- `start_date`
- `end_date`
- `category`
- `type`
- `search`
- `include_deleted` (admin only)
- `page`
- `limit`

Create permissions:

- `admin`: can create for self by default, or for another user using `POST /transactions?user_id=<id>`
- `analyst`: cannot create transactions
- `viewer`: cannot create transactions

### Dashboard

- `GET /dashboard/summary`
- `GET /dashboard/categories`
- `GET /dashboard/trends?group_by=month|week`
- `GET /dashboard/recent`

Dashboard endpoints are scoped to the authenticated user, so each user only sees their own transactions.

## RBAC Rules

- `viewer`: dashboard-only access
- `analyst`: read only their own transactions + dashboard access
- `admin`: full access to users, transactions, and dashboard

### Role Permission Matrix

| Area | Viewer | Analyst | Admin |
|---|---|---|---|
| Register/Login | Can register and login | Can login | Can login |
| Dashboard (`/dashboard/*`) | Can access | Can access | Can access |
| Dashboard data scope | Own data only | Own data only | Own data only |
| Create transaction (`POST /transactions`) | No (`403`) | No (`403`) | Yes, self by default, or any user via `?user_id=<id>` |
| List transactions (`GET /transactions`) | No (`403`) | Yes, own only | Yes, all |
| Get transaction by id (`GET /transactions/{id}`) | No (`403`) | Yes, own only | Yes, all |
| Include deleted (`include_deleted=true`) | No | No | Yes |
| Update transaction (`PUT /transactions/{id}`) | No | No | Yes |
| Delete transaction (`DELETE /transactions/{id}`) | No | No | Yes |
| Restore transaction (`PATCH /transactions/{id}/restore`) | No | No | Yes |
| User management (`/users` endpoints) | No | No | Yes |

Deleted transactions stay in the database with `is_deleted=true`. Admins can retrieve them with `include_deleted=true` and restore them with `PATCH /transactions/{id}/restore`.

RBAC is enforced through reusable dependencies rather than hardcoded checks inside route bodies.

## Assumptions And Trade-Offs

- New self-registered users always start as `viewer`.
- The first admin is bootstrapped from environment variables on startup.
- Tables are created automatically on startup to keep the project lightweight; Alembic is intentionally omitted in v1.
- Rate limiting is intentionally skipped to keep the initial implementation focused and maintainable.
- Dashboard aggregations are performed in SQL, not Python loops.
