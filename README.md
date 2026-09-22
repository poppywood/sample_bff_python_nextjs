# FastAPI BFF + Next.js starter

This repository contains a small browser-facing BFF starter with:

- `bff/` – FastAPI BFF for Auth0 login, Redis-backed browser sessions, CSRF protection, and proxying.
- `service_a/` – sample downstream FastAPI service protected by short-lived BFF-issued RS256 JWTs.
- `service_b/` – second sample downstream FastAPI service protected by short-lived BFF-issued RS256 JWTs.
- `libs/service_common/` – shared library used by `service_a` and `service_b` (currently: internal JWT verification/auth dependency).
- `frontend/` – Next.js App Router example that logs in through the BFF and reads/writes sample data only through the BFF.
- `keys/` – local development location for internal RS256 signing keys.

## Architecture

- The browser authenticates with Auth0 through the BFF.
- The BFF stores browser session state in Redis and sets an `HttpOnly` session cookie.
- The BFF issues a separate short-lived internal RS256 JWT when calling downstream services.
- `service_a` validates the BFF-issued JWT and never trusts browser cookies or Auth0 tokens directly.
- Mutating BFF routes require an `X-CSRF-Token` header that matches the server-side session token.

## Repository layout

```text
bff/
service_a/
service_b/
libs/service_common/
frontend/
keys/
docker-compose.yml
README.md
```

## Prerequisites

- Python 3.12+
- Node.js 22+
- npm 10+
- Redis 7+
- Auth0 tenant and regular web application
- OpenSSL for development key generation

## 1. Generate internal RS256 keys

The BFF signs internal service tokens with the private key in `keys/`, and `service_a` verifies them with the public key.

```bash
mkdir -p keys
openssl genrsa -out keys/internal_private.pem 2048
openssl rsa -in keys/internal_private.pem -pubout -out keys/internal_public.pem
```

Generated `.pem` files are gitignored.

## 2. Start Redis

Use local Redis or the included compose file:

```bash
docker compose up -d redis
```

## 3. Configure Auth0

Create an Auth0 Regular Web Application and set:

- **Allowed Callback URLs**: `http://localhost:8000/auth/callback`
- **Allowed Logout URLs**: `http://localhost:3000`
- **Allowed Web Origins**: `http://localhost:3000`

If you want roles copied into the internal JWT, expose them in a claim such as `https://example.com/roles` and set `AUTH0_ROLES_CLAIM` to match.

Suggested exact Auth0 checklist
Use this exact checklist:

Create Regular Web Application
Copy:
- Domain
- Client ID
- Client Secret

Set callback URL:
- http://localhost:8000/auth/callback

Set logout URL:
- http://localhost:3000

Set web origin:
- http://localhost:3000

Enable at least one login connection

Create a test user

Optionally create roles

Optionally add Post-Login Action for namespaced roles claim

Put values into BFF .env

Run Redis, service, BFF, frontend

Test login end-to-end

## 4. Configure environment files

### `bff/.env`

Copy `bff/.env.example`, fill in the Auth0 values, and replace `OAUTH_STATE_SECRET` with a real random secret before starting the BFF.
Leave `SESSION_COOKIE_DOMAIN` empty for the default localhost setup; set it to a shared parent domain when the frontend and BFF run on different hosts under the same site.

### `service_a/.env`

Copy `service_a/.env.example`.

### `service_b/.env`

Copy `service_b/.env.example`.

### `frontend/.env.local`

Copy `frontend/.env.local.example`.

## 5. Install dependencies

Create and use a separate virtual environment inside each Python project so the BFF and downstream services keep their dependencies isolated.

### BFF

```powershell
python -m venv bff\.venv
bff\.venv\Scripts\Activate.ps1
python -m pip install -r bff\requirements.txt
```

### Downstream service

`service_a\requirements.txt` installs the shared `libs/service_common` package in editable mode, so run `pip install` from the repository root so the relative path resolves correctly.

```powershell
python -m venv service_a\.venv
service_a\.venv\Scripts\Activate.ps1
python -m pip install -r service_a\requirements.txt
```

### Second downstream service

`service_b\requirements.txt` also installs `libs/service_common` in editable mode; run `pip install` from the repository root.

```powershell
python -m venv service_b\.venv
service_b\.venv\Scripts\Activate.ps1
python -m pip install -r service_b\requirements.txt
```

### Frontend

Use npm in the Next.js project directory to install the dependencies from `frontend\package.json` and generate or update `frontend\package-lock.json`.

```powershell
cd frontend
npm install
cd ..
```

## 6. Run the apps

### `service_a`

```bash
python -m uvicorn service_a.app.main:app --reload --port 8001 --env-file service_a/.env
```

### `bff`

```bash
python -m uvicorn bff.app.main:app --reload --port 8000 --env-file bff/.env
```

### `service_b`

```bash
python -m uvicorn service_b.app.main:app --reload --port 8002 --env-file service_b/.env
```

### `frontend`

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Example flows

- `GET /auth/login` – start Auth0 login.
- `GET /auth/callback` – handle Auth0 callback, create Redis session, set cookies, redirect to the frontend.
- `POST /auth/logout` – require CSRF header, clear Redis session, and return the Auth0 logout URL.
- `GET /me` – return the current user and CSRF token.
- `GET|POST /api/service-a/orders` – proxy order requests through the BFF with a short-lived internal JWT.
- `GET|POST /api/service-b/notes` – proxy note requests through the BFF with a short-lived internal JWT.

## Security notes

- Browser OAuth tokens are not stored in frontend storage.
- The browser never talks directly to `service_a` or `service_b`.
- Internal service JWTs are scoped to a different issuer/audience than Auth0 tokens.
- `SESSION_SECURE_COOKIES=false` is for local HTTP development only; turn it on under HTTPS.
- Auth0 credentials and generated keys must stay local and must not be committed.

## Shared library (`libs/service_common`)

`service_a` and `service_b` both need to verify BFF-issued internal JWTs the same way, so that logic lives in `libs/service_common/service_common/auth.py` instead of being duplicated per service:

- `AuthenticatedUser` – shared pydantic model for the decoded token claims.
- `require_authenticated_user` – FastAPI dependency that validates the `Authorization: Bearer` header against `INTERNAL_JWT_PUBLIC_KEY_PATH`, `INTERNAL_JWT_ISSUER`, and `INTERNAL_JWT_AUDIENCE`.

Each service still sets its own `INTERNAL_JWT_AUDIENCE` in its `.env` file, so the shared dependency behaves per-service without any code duplication. Both `service_a/requirements.txt` and `service_b/requirements.txt` install `libs/service_common` with `pip install -e ./libs/service_common`, so any change to the shared library is picked up immediately by both services without reinstalling. Add future cross-service code (e.g. shared models, Redis helpers) to `libs/service_common` rather than copying it between services.

## Local development tips

- Redis session keys use the `bff:session:` prefix.
- `service_a` stores sample orders in Redis by default (`redis://localhost:6379/1`) so its data stays consistent across workers/processes.
- `service_b` stores sample notes in Redis by default (`redis://localhost:6379/2`) so its data stays consistent across workers/processes.
- If Auth0 roles are not configured, the starter safely falls back to an empty roles list.
