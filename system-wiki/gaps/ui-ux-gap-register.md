---
title: UI/UX Gap Register
created: 2026-05-14
updated: 2026-05-15
type: gap
tags: [wims-bfp, gap, ui-ux, needs-verification]
sources: [raw/ui-ux, ui-ux/evaluation-loginpage-keycloaksso.md, ui-ux/evaluation-system-admin-hub.md, ui-ux/evaluation-national-analyst.md]
status: needs-review
---

# UI/UX Gap Register

UI/UX improvement gaps identified during user desk-check evaluations (2026-05-14). Functional/auth bugs are in [[gaps/functional-bug-register]].

## Login Page + Keycloak SSO (`/login`)
| Issue | Detail | Status |
|---|---|---|
| Sign-in container misalignment | Hero section and sign-in form are vertically stacked/misaligned on desktop | Needs implementation |
| Hero icon loss on Keycloak redirect | After Keycloak redirect, hero illustration/icon disappears | Needs implementation |
| TOTP digit-separation UX | 6-box TOTP input with auto-advance and backspace behavior; no visual digit grouping | Needs implementation |

Source: [[ui-ux/evaluation-loginpage-keycloaksso]]

## System Admin Hub (`/admin`)
| Issue | Detail | Status |
|---|---|---|
| Linear vertical flow | Cards stacked vertically — wastes horizontal space; should use grid/HCI card layout | Needs implementation |
| Missing M9 metrics | No VPS usage, container status, PWA sync status, AI model latency, DB query latency cards | Needs implementation |
| Technology heartbeat charts | No live health charts for monitored components | Needs implementation |
| Tabbed Activity & Governance | Activity log and governance controls should be tabbed, not separate pages | Needs implementation |
| Region selector UX | Uses increment/decrement instead of dropdown populated from `ref_regions` | Needs implementation |
| No pagination | Admin hub lists (users, incidents) lack pagination controls | Needs implementation |
| No full-text filter/search | No search bar for filtering lists | Needs implementation |
| Regional heatmap missing on `/home` | Per-role heatmap not rendered for any role | Needs implementation |
| No system-wide announcement feature | No banner/toast for global announcements visible on `/home` | Needs implementation |
| Configuration Management (M9.c) | No UI for setting M9 monitoring thresholds | Needs implementation |
| Modal consolidation | Excessive modals; should redirect to detail pages instead | Needs implementation |

Source: [[ui-ux/evaluation-system-admin-hub]]

## Home Page (`/home`)
| Issue | Detail | Status |
|---|---|---|
| Missing regional heatmap | Per-role heatmap not rendered for any role | Needs implementation |
| No system-wide announcement feature | No banner/toast for global announcements | Needs implementation |

## National Analyst Dashboard (`/dashboard/analyst`)
| Issue | Detail | Status |
|---|---|---|
| Heatmap aspect ratio wrong | Wide full-width heatmap; should be tall/portrait and side-positioned | Fixed in code; needs browser verification |
| Filter bar sizing | Filters should be larger and more prominent than "All Synced" badge | Fixed in code; needs browser verification |
| No incident container/list | No dedicated panel for individual incidents | Fixed in code; needs UI verification |
| Side panel non-functional | Incident detail side panel redirects back to dashboard | Fixed in code; needs UI verification |
| Filter missing columns | Filters do not cover all FRS M5.a.ii required fields (date range, casualty severity, property damage, location) | Core M5 filters fixed in code; wildfire-specific filters deferred |
| Export has no preview container | Export PDF/Excel buttons export immediately without a preview/filters container | Fixed in code; needs browser verification |
| Top municipalities view missing | FRS M5.a.iii requires "Top 10 municipalities" analytics view | Fixed in code; needs browser verification |
| Average response time by region missing | FRS M5.a.iii requires "Average response time by region" view | Fixed in code; needs browser verification |
| Analyst sidebar missing | No explicit `NATIONAL_ANALYST` section in `Sidebar.tsx` | Fixed in code; needs UI verification |
| Export backend incomplete | PDF/XLSX/download/audit backend infrastructure missing | Fixed in code; verify Celery retention/cleanup before production |
| Analyst detail/wildland routes missing | No read-only analyst full-page incident detail or wildland detail route | Fixed in code; needs UI verification |
| Dashboard scanability and incident-list failure state | Dashboard did not provide enough at-a-glance context, and the incident list surfaced raw 500 text during backend failures | Fixed in code; needs browser verification |
| Dedicated analyst workflow pages missing | Major dashboard functions had no focused pages for deeper controls, exports, calculations, and incident evidence | Fixed in code via `/dashboard/analyst/[workflow]`; needs browser verification |
| Incident list selection/export workflow | Incident list should be prominent, persist selected records across pagination, support selected-record CSV/PDF column-selection export, and provide separate full AFOR export with all AFOR fields; multi-incident full PDF should be one file with one incident per page/section | Phase 1 UI/selection fixed in code; Phase 2 modular export backend remains |

Source: [[ui-ux/evaluation-national-analyst]]

## Related
- [[ui-ux/evaluation-loginpage-keycloaksso]]
- [[ui-ux/evaluation-system-admin-hub]]
- [[concepts/frs-module-map]]
- [[gaps/functional-bug-register]]
