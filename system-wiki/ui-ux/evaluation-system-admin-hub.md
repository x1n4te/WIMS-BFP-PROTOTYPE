---
title: System Admin Hub — UI/UX Evaluation
created: 2026-05-14
updated: 2026-05-14
type: ui-ux
tags: [wims-bfp, ui-ux, admin, hci, monitoring, system-monitoring]
sources: [raw/ui-ux/evaluation-system-admin-hub.md, raw/frs/frs-auth.md, raw/frs/frs-systemmonitoringandhealthdashboard.md, raw/frs/frs-intrusiondetectionandnetworkingmonitoring.md]
status: needs-review
---

# System Admin Hub — UI/UX Evaluation

Desk-check findings from user evaluation of the System Administrator dashboard and health monitoring interface.

## Layout Issues

### Current Problem: Linear Vertical Flow
The admin hub currently renders as a single-column downward flow. This wastes horizontal space and buries unrelated metrics. The goal is a full HCI-optimized dashboard with card-based spatial organization.

### "All Synced" Bar — Refactor to System Integrity Card
The top-of-page status bar should become a `System Integrity` card positioned adjacent to Key Metrics. It should contain:
- Total Users over time (trend chart)
- Active Sessions (bar chart)
- Total API Requests over time (trend chart)

## Missing Monitoring Metrics (M9 FRS Alignment)
Per FRS Module 9 (System Monitoring and Health Dashboard), the following are not yet implemented and must be added:

| Metric | FRS M9 spec | Status |
|---|---|---|
| VPS Resource Usage (CPU/RAM) | M9.a.i — real-time utilization | Not implemented |
| Container Status (FastAPI, PostgreSQL, Suricata, Qwen-AI) | M9.a.i — uptime and health | Not implemented |
| PWA Sync Health | M9.a.i — background sync success rate | Not implemented |
| Network Traffic | M9.a.i — inbound/outbound bandwidth via Nginx | Not implemented |
| AI On-Demand Latency | M9.a.i — SLM inference time per request | Not implemented |
| Database Query Latency | M9.a.i — average query latency in ms | Not implemented |
| Metrics refresh interval | M9.a.ii — every 60 seconds | Not implemented |

**FRS source:** [[raw/frs/frs-systemmonitoringandhealthdashboard]]

## System Health — Technology Status Cards
Each active technology should display a live fluctuating heartbeat-style chart:
- Keycloak (identity provider)
- PostgreSQL (database)
- Redis (notifications/cache)
- Suricata (IDS)
- Nginx (reverse proxy)

## Identity Governance -> Activity & Governance (Tabbed Container)
The Identity Governance section should be renamed `Activity & Governance` and implemented as a tabbed container with tabs for:
- Users
- Sessions
- Active connections

### Modal Consolidation
Pressing the session icon on a user row currently opens a modal listing IP addresses and a "Terminate All" button. This should redirect to the full Active Sessions view instead. The Active Sessions list must include:
- Browser being used
- OS of connected session
- IP address
- Session start time
- Terminate individual session action

### Edit User — Region Selector
The edit user action currently uses increment/decrement controls for `region_id`. Since `postgres-init` seeds region data in SQL, the region field should use a dropdown/select component populated from `wims.ref_regions`. Do not use numeric increment/decrement.

### Pagination
No pagination is applied to the user/session tables. All tables exceeding ~20 rows must be paginated.

### Filters
The following admin views are missing filter controls entirely:
- System Audit Logs
- Threat Telemetry (Suricata EVE JSON logs)
- Active Sessions
- Identity Governance user list

Per FRS M9.b.iii: Full-text search across log entries (PostgreSQL tsvector with Gin Index) must be implemented.

## /home Role Dashboard Additions
Since `/home` serves all roles, each role-specific home page should include:
- A heatmap filtered to their assigned region only (for Regional Encoder, National Validator, National Analyst)

## Announce Feature (System-Wide Notification)
A new system-wide announcement feature is needed. The System Administrator can post maintenance windows, emergency operations notices, or policy announcements. The announcement banner should render at the top of the `/home` page for all authenticated roles.

Implementation scope: new table in schema, admin write endpoint, frontend banner component with dismiss capability.

## Configuration Management (M9.c — Not Implemented)
Per FRS M9.c, System Administrators must be able to update monitoring thresholds via the interface:
- Alert severity thresholds (e.g., trigger High alert if >5 failed logins in 10 minutes)
- Session timeout duration
- Offline mode maximum storage limit
- AI Response Timeout (maximum time before SLM inference is cancelled)

## Related
- [[security/security-baseline]] — security monitoring and IDS alignment
- [[frontend/route-map]] — admin page route mapping
- [[database/schema-overview]] — audit log and session tables
- [[raw/ui-ux/evaluation-system-admin-hub]] (raw source)