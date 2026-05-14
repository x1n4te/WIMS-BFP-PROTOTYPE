---
title: Frontend Route Map
created: 2026-05-14
updated: 2026-05-14
type: frontend
tags: [wims-bfp, frontend, routing, implementation-map]
sources: [raw/codebase/codebase-snapshot-2026-05-14.md, src/frontend/src/app]
status: draft
---

# Frontend Route Map

Next.js App Router pages detected under `src/frontend/src/app`.

| Route | Source file |
|---|---|
| `/admin` | `admin/page.tsx` |
| `/admin/system` | `admin/system/page.tsx` |
| `/afor/create` | `afor/create/page.tsx` |
| `/afor/import` | `afor/import/page.tsx` |
| `/callback` | `callback/page.tsx` |
| `/dashboard/analyst` | `dashboard/analyst/page.tsx` |
| `/dashboard` | `dashboard/page.tsx` |
| `/dashboard/regional/audit` | `dashboard/regional/audit/page.tsx` |
| `/dashboard/regional/drafts` | `dashboard/regional/drafts/page.tsx` |
| `/dashboard/regional/incidents/[id]` | `dashboard/regional/incidents/[id]/page.tsx` |
| `/dashboard/regional` | `dashboard/regional/page.tsx` |
| `/dashboard/validator/audit` | `dashboard/validator/audit/page.tsx` |
| `/dashboard/validator` | `dashboard/validator/page.tsx` |
| `/home` | `home/page.tsx` |
| `/incidents/[id]` | `incidents/[id]/page.tsx` |
| `/incidents/create` | `incidents/create/page.tsx` |
| `/incidents/import` | `incidents/import/page.tsx` |
| `/incidents/new` | `incidents/new/page.tsx` |
| `/incidents` | `incidents/page.tsx` |
| `/incidents/triage` | `incidents/triage/page.tsx` |
| `/login` | `login/page.tsx` |
| `/` | `page.tsx` |
| `/profile` | `profile/page.tsx` |
| `/report` | `report/page.tsx` |
| `/report/track` | `report/track/page.tsx` |

## UI Surface Clusters
- Auth/profile: `/login`, `/callback`, `/profile`, auth API routes.
- Incident entry/import: `/incidents/*`, `/afor/*`, regional dashboard pages.
- Validation: `/dashboard/validator`, `/dashboard/validator/audit`, `/incidents/triage`.
- Analytics/reporting: `/dashboard/analyst`, `/report`, `/report/track`. The sidebar now has an explicit `NATIONAL_ANALYST` navigation section pointing to `/dashboard/analyst` and `/profile`; analyst incident detail routes are still pending.
- Administration/security: `/admin`, `/admin/system`.

## Related
- [[backend/api-route-map]]
- [[concepts/frs-module-map]]
