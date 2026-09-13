# FastAPI BFF + Next.js starter

This repository contains a small browser-facing BFF starter with:

- `bff/` – FastAPI BFF for Auth0 login, Redis-backed browser sessions, CSRF protection, and proxying.
- `service_a/` – sample downstream FastAPI service protected by short-lived BFF-issued RS256 JWTs.
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

### `frontend/.env.local`

Copy `frontend/.env.local.example`.

## 5. Install dependencies

Create and use a separate virtual environment inside each Python project so the BFF and downstream service keep their dependencies isolated.

### BFF

```powershell
python -m venv bff\.venv
bff\.venv\Scripts\Activate.ps1
python -m pip install -r bff\requirements.txt
```

### Downstream service

```powershell
python -m venv service_a\.venv
service_a\.venv\Scripts\Activate.ps1
python -m pip install -r service_a\requirements.txt
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
- `GET|POST /api/service-a/orders` – proxy through the BFF with a short-lived internal JWT.

## Security notes

- Browser OAuth tokens are not stored in frontend storage.
- The browser never talks directly to `service_a`.
- Internal service JWTs are scoped to a different issuer/audience than Auth0 tokens.
- `SESSION_SECURE_COOKIES=false` is for local HTTP development only; turn it on under HTTPS.
- Auth0 credentials and generated keys must stay local and must not be committed.

## Local development tips

- Redis session keys use the `bff:session:` prefix.
- `service_a` stores sample orders in Redis by default (`redis://localhost:6379/1`) so its data stays consistent across workers/processes.
- If Auth0 roles are not configured, the starter safely falls back to an empty roles list.
