# WIMS-BFP Frontend

Next.js App Router application for the WIMS-BFP incident management platform.

## Stack

- **Framework:** Next.js 14+ with TypeScript
- **Auth:** Keycloak OIDC via `next-auth` — all pages behind authentication
- **Styling:** Tailwind CSS + shadcn/ui components
- **Maps:** Leaflet / React-Leaflet for geospatial incident display
- **State:** React Context + hooks; no Redux
- **Testing:** Vitest + React Testing Library

## Environment Variables

Required in `src/.env`:

```env
NEXT_PUBLIC_API_URL=http://localhost/api
NEXT_PUBLIC_AUTH_API_URL=http://localhost:8080/auth
NEXT_PUBLIC_BASE_URL=http://localhost
NEXT_PUBLIC_OIDC_AUTHORITY=http://localhost:8080/auth/realms/bfp
NEXT_PUBLIC_OIDC_REDIRECT_URI=http://localhost/callback
```

These are pre-configured in `docker-compose.yml` for local Docker runs. For local non-Docker development, copy `.env.example` from the repo root into `src/.env`.

## Running

```bash
cd src/frontend
npm install
npm run dev      # development server at http://localhost
npm run build    # production build
npm run lint     # ESLint
npx vitest run   # tests
```

## Routing Conventions

- `app/` — App Router pages and layouts. No `pages/` directory.
- Route groups with `(auth)` prefix are unauthenticated layouts (login, callback).
- All other routes require a valid Keycloak session — middleware redirects unauthenticated requests to `/auth/signin`.
- API proxy at `/api/*` rewrites to FastAPI backend (`/api/regional/incidents`, `/api/admin/...`, etc.).

## Key Directories

| Path | Purpose |
|------|---------|
| `app/` | Next.js App Router pages and layouts |
| `components/` | Reusable React components (UI, map, forms) |
| `context/` | React Context providers (Auth, Map) |
| `lib/` | Client-side utilities (auth, API client) |
| `hooks/` | Custom React hooks |
| `public/` | Static assets, AFOR templates |

## Auth Flow

1. User visits any protected route
2. Middleware checks for `next-auth.session-token` cookie
3. If missing, redirects to Keycloak login (`/auth/signin`)
4. After login, Keycloak redirects to `/callback` with OIDC code
5. `next-auth` exchanges code for session token
6. User lands on original requested route

## Testing

```bash
npx vitest run          # run all tests once
npx vitest run --watch  # watch mode
```

Tests live alongside components: `components/MapPicker.test.tsx`, `hooks/useIncidents.test.ts`, etc.