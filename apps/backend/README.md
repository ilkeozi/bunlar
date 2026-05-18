# Backend (`@bunlar/backend`)

NestJS backend application in the Nx workspace.

## Quick Start

From workspace root:

```bash
# Install dependencies
npm install

# Start backend (development)
npx nx serve backend
```

Default base URL:

- `http://localhost:3000/api/v1`

## Core Commands

From workspace root:

```bash
# Lint (strict, warnings fail)
npx nx lint backend

# Build (depends on lint)
npx nx build backend

# Unit tests
npx nx test backend
```

## Docker

Build image from workspace root:

```bash
docker build -f apps/backend/Dockerfile -t bunlar-backend:local .
```

Run container:

```bash
docker run --rm -p 3000:3000 --env-file apps/backend/.env.local bunlar-backend:local
```

If you do not have `.env.local` yet:

```bash
cp apps/backend/.env.example apps/backend/.env.local
```

Run full stack (frontend + backend):

```bash
cp .env.compose.example .env.compose
cp apps/backend/.env.example apps/backend/.env.local
docker compose --env-file .env.compose up --build -d
```

Stack endpoints (example):

- Frontend: `http://localhost:<FRONTEND_PORT>`
- Backend API: `http://localhost:<BACKEND_PORT>/api/v1`
- Swagger: `http://localhost:<BACKEND_PORT>/api/docs`
- PostgreSQL: `localhost:<POSTGRES_PORT>` (from host)
- Redis: `localhost:<REDIS_PORT>` (from host)

PostgreSQL in compose:

- Service name (inside Docker network): `postgres`
- Database: `<POSTGRES_DB>`
- User: `<POSTGRES_USER>`
- Password: `<POSTGRES_PASSWORD>`

When backend runs in compose, it uses:

- `DATABASE_URL=postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@postgres:5432/<POSTGRES_DB>`
- `REDIS_ENABLED=true`
- `REDIS_HOST=redis`
- `REDIS_PORT=6379`

## API Endpoints

- Health (liveness): `GET /api/v1/health/live` (process-level)
- Health (readiness): `GET /api/v1/health/ready` (PostgreSQL + Redis probes)
- Swagger UI (default): `GET /api/docs`

## Environment Configuration

Use `apps/backend/.env.example` as the template:

```bash
cp apps/backend/.env.example apps/backend/.env.local
```

Available env vars:

- `NODE_ENV`: `development | test | production`
- `PORT`: HTTP port
- `GLOBAL_PREFIX`: global API prefix (default `api`)
- `API_VERSION`: URI version segment (default `1`)
- `CORS_ORIGIN`: `*` or comma-separated origins
- `TRUST_PROXY`: numeric trust proxy setting
- `THROTTLE_TTL_MS`: rate-limit window in ms
- `THROTTLE_LIMIT`: max requests per window
- `CACHE_TTL_SECONDS`: default cache TTL
- `CACHE_MAX_ITEMS`: in-memory cache size limit
- `SWAGGER_ENABLED`: `true | false`
- `SWAGGER_PATH`: docs path under global prefix (default `docs`)
- `SWAGGER_TITLE`: Swagger title
- `SWAGGER_DESCRIPTION`: Swagger description
- `DATABASE_URL`: PostgreSQL connection URL
- `REDIS_ENABLED`: enable Redis cache store (`true | false`)
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `REDIS_PASSWORD`: Redis password (optional)
- `REDIS_DB`: Redis DB index

## Security + Platform Defaults

Configured in `src/main.ts` and `src/app/app.module.ts`:

- `helmet` for common HTTP hardening headers
- CORS with configurable origin list
- CSRF middleware (`csurf`) + cookie parser
- Global rate limiting (`@nestjs/throttler`)
- Global caching (`@nestjs/cache-manager`)
- Redis-backed caching when enabled (`cache-manager-ioredis-yet` + `ioredis`)
- API versioning (`VersioningType.URI`)

## Linting Policy

Backend lint is strict:

- `apps/backend/package.json` defines:
  - `lint`: `eslint . --max-warnings=0`
  - `build` depends on `lint`
- Build fails if lint fails.

## Project Structure

```txt
apps/backend/
  src/
    main.ts
    app/
      app.module.ts
      app.controller.ts
      app.service.ts
      config/
        env.validation.ts
      modules/
        health/
          health.module.ts
          health.controller.ts
```

## Notes

- This backend currently uses workspace-level dependencies.
- If a module import error appears during build, run `npm install` at workspace root.
