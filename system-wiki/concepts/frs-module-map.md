---
title: FRS Module Map
created: 2026-05-14
updated: 2026-05-14
type: concept
tags: [wims-bfp, frs, implementation-map]
sources: [raw/frs]
status: needs-review
---

# FRS Module Map

This page maps the 15 agreed FRS modules to current implementation anchors. It is a routing index, not proof of full completion.

| Module | Name | FRS source | Current code anchors / verification targets |
|---:|---|---|---|
| M1 | Authentication and Access Control | `raw/frs/frs-auth.md` | admin.py, sessions.py, user.py, frontend auth routes |
| M2 | Offline-First Incident Management | `raw/frs/frs-offlinefirst.md` | incidents.py, regional.py, offlineStore.ts, syncEngine.ts |
| M3 | Conflict Detection and Manual Verification | `raw/frs/frs-conflictdetectionandmanualverification.md` | triage.py, regional.py validator endpoints |
| M4 | Data Commit and Immutable Storage | `raw/frs/frs-datacommitandimmutablestorage.md` | regional.py verification endpoints, 17_immutable_records.sql |
| M5 | Analytics and Reporting | `raw/frs/frs-analyticsandreporting.md` | analytics.py, admin scheduled reports, analytics SQL |
| M6 | Cryptographic Security | `raw/frs/frs-cryptographicsecurity.md` | utils/crypto.py, hash/audit paths; FRS source empty |
| M7 | Intrusion Detection and Network Monitoring | `raw/frs/frs-intrusiondetectionandnetworkingmonitoring.md` | suricata/, admin security logs |
| M8 | Threat Detection with Explainable AI (XAI) | `raw/frs/frs-threatdetectionwithexplainableai.md` | services/ai_service.py, admin analyze endpoint |
| M9 | System Monitoring and Health Dashboard | `raw/frs/frs-systemmonitoringandhealthdashboard.md` | admin.py health endpoint; FRS source empty |
| M10 | Compliance and Data Privacy | `raw/frs/frs-complianceanddataprivacy.md` | RLS, soft delete/audit, privacy docs required |
| M11 | Penetration Testing and Security Validation | `raw/frs/frs-penentrationtestingandsecurityvalidation.md` | procedure/docs, not primarily code |
| M12 | User Management and Administration | `raw/frs/frs-usermanagementandadministration.md` | admin.py users, user.py profile/password |
| M13 | Notification System | `raw/frs/frs-notificationsystem.md` | SSE/Redis/email paths need deep scan |
| M14 | Public Anonymous Incident Submission | `raw/frs/frs-publicanonymousincidentsubmission.md` | public_dmz.py, triage.py; FRS source empty |
| M15 | Reference Data Service | `raw/frs/frs-referencedataservice.md` | ref.py, ref_* tables, RLS policies |

## Usage
- For backend work, start with this page then read [[backend/api-route-map]].
- For database/RLS work, continue to [[database/schema-overview]].
- For security-impacting work, continue to [[security/security-baseline]].

## Caution
Some FRS source files are empty in the supplied batch. Do not infer requirements from absence. Track them in [[gaps/frs-codebase-gap-register]].
