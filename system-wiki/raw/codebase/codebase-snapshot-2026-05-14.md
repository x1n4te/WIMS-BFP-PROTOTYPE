# Codebase Snapshot — 2026-05-14

Source root: `/home/xynate/WIMS-BFP-NEW/LOCAL-WIMS-BFP-PROTOTYPE`
Branch state observed: `master...origin/master`; untracked `wiki-dir/` before system wiki creation.
Remote: `https://github.com/x1n4te/WIMS-BFP-PROTOTYPE.git`

## Backend API Routes
| File | Method | Path | Function |
|---|---:|---|---|
| `civilian.py` | `POST` | `/reports` | `submit_civilian_report` |
| `civilian.py` | `GET` | `/reports/{report_id}` | `get_civilian_report` |
| `sessions.py` | `GET` | `/sessions/{user_id}` | `list_user_sessions` |
| `sessions.py` | `DELETE` | `/sessions/{user_id}/{session_id}` | `terminate_user_session` |
| `user.py` | `GET` | `/me/profile` | `get_my_profile` |
| `user.py` | `PATCH` | `/me` | `update_my_profile` |
| `user.py` | `PATCH` | `/me/password` | `change_my_password` |
| `ref.py` | `GET` | `/regions` | `get_regions` |
| `ref.py` | `GET` | `/provinces` | `get_provinces` |
| `ref.py` | `GET` | `/cities` | `get_cities` |
| `incidents.py` | `POST` | `/incidents/upload-bundle` | `upload_incident_bundle` |
| `incidents.py` | `POST` | `/incidents/{incident_id}/attachments` | `upload_attachment` |
| `incidents.py` | `POST` | `/incidents` | `create_incident` |
| `incidents.py` | `GET` | `/incidents` | `get_incidents` |
| `regional.py` | `POST` | `/afor/import` | `import_afor_file` |
| `regional.py` | `POST` | `/afor/commit` | `commit_afor_import` |
| `regional.py` | `GET` | `/incidents` | `get_regional_incidents` |
| `regional.py` | `GET` | `/incidents/drafts` | `list_encoder_drafts` |
| `regional.py` | `GET` | `/incidents/check-duplicate` | `check_incident_duplicate` |
| `regional.py` | `GET` | `/incidents/{incident_id}` | `get_regional_incident_detail` |
| `regional.py` | `GET` | `/validator/stats` | `get_validator_stats` |
| `regional.py` | `GET` | `/stats` | `get_regional_stats` |
| `regional.py` | `POST` | `/incidents` | `create_incident` |
| `regional.py` | `PUT` | `/incidents/{incident_id}` | `update_incident` |
| `regional.py` | `POST` | `/incidents/{incident_id}/force-replace` | `force_replace_incident` |
| `regional.py` | `PATCH` | `/incidents/draft/{incident_id}` | `update_draft` |
| `regional.py` | `DELETE` | `/incidents/draft/{incident_id}` | `delete_draft` |
| `regional.py` | `PATCH` | `/incidents/{incident_id}/unpend` | `unpend_incident` |
| `regional.py` | `DELETE` | `/incidents/{incident_id}` | `delete_incident` |
| `regional.py` | `PATCH` | `/incidents/{incident_id}/submit` | `submit_incident_for_review` |
| `regional.py` | `GET` | `/validator/incidents` | `get_validator_incident_queue` |
| `regional.py` | `PATCH` | `/incidents/{incident_id}/verification` | `verify_incident` |
| `regional.py` | `POST` | `/validator/incidents/bulk-approve` | `bulk_approve_incidents` |
| `regional.py` | `PATCH` | `/validator/incidents/{incident_id}/archive` | `archive_incident` |
| `regional.py` | `GET` | `/validator/incidents/{incident_id}/diff` | `get_incident_diff` |
| `regional.py` | `GET` | `/audit-log` | `get_encoder_audit_log` |
| `regional.py` | `GET` | `/validator/audit-logs` | `get_validator_audit_logs` |
| `regional.py` | `GET` | `/validator/audit-logs/export` | `export_validator_audit_logs` |
| `triage.py` | `GET` | `/pending` | `get_pending_reports` |
| `triage.py` | `POST` | `/{report_id}/promote` | `promote_report` |
| `triage.py` | `POST` | `/bulk-promote` | `bulk_promote_reports` |
| `admin.py` | `POST` | `/users` | `create_user` |
| `admin.py` | `GET` | `/users` | `get_users` |
| `admin.py` | `PATCH` | `/users/{user_id}` | `update_user` |
| `admin.py` | `GET` | `/active-sessions` | `get_active_sessions` |
| `admin.py` | `POST` | `/users/{user_id}/logout` | `force_logout_user` |
| `admin.py` | `GET` | `/health` | `get_system_health` |
| `admin.py` | `GET` | `/security-logs` | `get_security_logs` |
| `admin.py` | `POST` | `/security-logs/{log_id}/analyze` | `analyze_security_log` |
| `admin.py` | `PATCH` | `/security-logs/{log_id}` | `update_security_log` |
| `admin.py` | `POST` | `/analytics/backfill` | `backfill_analytics` |
| `admin.py` | `GET` | `/audit-logs` | `get_audit_logs` |
| `admin.py` | `POST` | `/scheduled-reports` | `create_scheduled_report` |
| `admin.py` | `GET` | `/scheduled-reports` | `list_scheduled_reports` |
| `admin.py` | `POST` | `/backup` | `trigger_backup` |
| `admin.py` | `GET` | `/backups` | `list_backups` |
| `admin.py` | `GET` | `/backup/{filename}` | `download_backup` |
| `analytics.py` | `POST` | `/refresh-views` | `trigger_materialized_view_refresh` |
| `analytics.py` | `GET` | `/heatmap` | `get_heatmap` |
| `analytics.py` | `GET` | `/trends` | `get_trends_route` |
| `analytics.py` | `GET` | `/comparative` | `get_comparative` |
| `analytics.py` | `GET` | `/execution-plans` | `get_execution_plans` |
| `analytics.py` | `POST` | `/export/csv` | `export_csv` |
| `analytics.py` | `POST` | `/export/pdf` | `export_pdf` |
| `analytics.py` | `POST` | `/export/excel` | `export_excel` |
| `analytics.py` | `GET` | `/type-distribution` | `get_type_distribution_route` |
| `analytics.py` | `GET` | `/top-barangays` | `get_top_barangays_route` |
| `analytics.py` | `GET` | `/response-time-by-region` | `get_response_time_by_region_route` |
| `analytics.py` | `GET` | `/compare-regions` | `compare_regions_route` |
| `analytics.py` | `GET` | `/top-n` | `top_n_route` |
| `public_dmz.py` | `POST` | `/` | `submit_public_incident` |

## Database Tables Created by SQL Init Files
| Table | Source file |
|---|---|
| `wims.ref_regions` | `02_ref_geography.sql` |
| `wims.ref_provinces` | `02_ref_geography.sql` |
| `wims.ref_cities` | `02_ref_geography.sql` |
| `wims.ref_barangays` | `02_ref_geography.sql` |
| `wims.users` | `03_users.sql` |
| `wims.data_import_batches` | `04_import_incidents.sql` |
| `wims.fire_incidents` | `04_import_incidents.sql` |
| `wims.citizen_reports` | `05_citizen_reports.sql` |
| `wims.incident_attachments` | `06_incident_details.sql` |
| `wims.incident_nonsensitive_details` | `06_incident_details.sql` |
| `wims.incident_sensitive_details` | `06_incident_details.sql` |
| `wims.incident_verification_history` | `06_incident_details.sql` |
| `wims.involved_parties` | `06_incident_details.sql` |
| `wims.operational_challenges` | `06_incident_details.sql` |
| `wims.responding_units` | `06_incident_details.sql` |
| `wims.incident_wildland_afor` | `07_wildland_afor.sql` |
| `wims.wildland_afor_alarm_statuses` | `07_wildland_afor.sql` |
| `wims.wildland_afor_assistance_rows` | `07_wildland_afor.sql` |
| `wims.regional_public_keys` | `08_security_audit.sql` |
| `wims.security_threat_logs` | `08_security_audit.sql` |
| `wims.system_audit_trails` | `08_security_audit.sql` |
| `wims.analytics_incident_facts` | `11_analytics_facts.sql` |
| `wims.analytics_export_log` | `13_export_reports.sql` |
| `wims.scheduled_reports` | `13_export_reports.sql` |
| `wims.incident_verification_history` | `15_validator_workflow.sql` |
| `wims.reference_sequence` | `27_reference_sequence.sql` |

## Frontend App Routes
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

## Version Anchors
- Frontend: `src/frontend/package.json` reports Next `16.1.6`, React `19.2.3`, TypeScript `^5`, Vitest `^4.0.18`.
- Backend: `src/backend/pyproject.toml` reports Python `>=3.10`, Ruff line length `100`, target `py310`.
