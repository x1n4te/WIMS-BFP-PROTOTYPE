# WIMS-BFP – Deployment test checklist

Run this **once, in order, on the real server PC (or an identical x86 Windows test PC)** before
turnover. Nothing in the client package has been executed on Windows/Docker yet; this is the
first run. Write the result in the **Result** column (PASS / FAIL + note). A FAIL in sections
1–7 blocks the rest.

- **Server PC:** the Windows PC with Rancher Desktop. **Second device:** another PC (or laptop)
  on the same network, with the CA installed (section 10).
- `sql "<query>"` below means, in `C:\WIMS`:
  `docker compose exec -T postgres psql -U postgres -d wims -c "<query>"`
  and `sqlkc "<query>"` means the same with `-d keycloak`.
- Record: Windows version, RAM, CPU, Rancher Desktop version, bundle `VERSION.json`.

## 1. Bundle and runtime

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 1.1 | Runtime ready | `docker version`, `docker compose version`; Rancher: dockerd engine, Kubernetes off | both print versions | |
| 1.2 | Memory cap active | `.wslconfig` has `memory=4GB`; after `wsl --shutdown` and restart: `wsl -e free -m` | total ≈ 3.9 GB | |
| 1.3 | Bundle intact | `install.ps1` checksum step | every line `ok`; tamper test: change one byte in a copy → `CORRUPT`, install refuses | |
| 1.4 | Fixed IP and name | `ping wims.bfp.lan` from server **and** second device | answers from the server IP | |

## 2. Install from the bundle with the internet **disconnected**

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 2.1 | Offline install | Unplug internet (keep the LAN). `.\setup-secrets.ps1`, `.\install.ps1 -OpenFirewall` | finishes with "WIMS-BFP is running"; no pull attempts (`up --pull never`) | |
| 2.2 | Time to ready | note minutes from `up` to all healthy | ≤ 15 min | |
| 2.3 | Seven containers | `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"` | postgres, redis, keycloak, backend, celery-worker, frontend, nginx; postgres/redis/keycloak/backend/nginx `(healthy)` | |
| 2.4 | Only nginx publishes ports | same output | only `wims-nginx` has `0.0.0.0:80->80, 0.0.0.0:443->443` | |
| 2.5 | No removed services | `docker ps -a` | no openbao, suricata, ollama, osrm, mailhog | |
| 2.6 | Re-run is safe | `.\install.ps1` again (stack running) | backup taken first, same result, data untouched, "skipping" the administrator step | |

## 3. Fresh boot and migrations

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 3.1 | Init ran clean | `docker compose logs postgres \| findstr /i "ERROR FATAL"` | nothing except possibly harmless notices; log ends `client init: database role passwords set` | |
| 3.2 | Role passwords replaced | `docker run --rm --network wims_default -e PGPASSWORD=wimsapp --entrypoint psql wims-backend:client -h postgres -U wims_app_user -d wims -c "select 1"` and the same with `-e PGPASSWORD=secret -U keycloak -d keycloak` | both **fail** (password authentication failed) | |
| 3.3 | Alembic at head | `docker compose exec -T backend alembic current` | `0030 (head)` | |
| 3.4 | Backend start log | `docker compose logs backend \| findstr /i "alembic Skipping baseline Startup checks"` | "Core WIMS tables exist – skipping baseline bootstrap" (baseline must **not** have re-run seeds), "Startup checks done" | |
| 3.5 | Celery beat | `docker compose logs celery-worker \| findstr /i "beat Scheduler"`; no `ensure_pii_key_rotation` scheduled/erroring | beat started; no OpenBao/KMS errors | |
| 3.6 | Health endpoint | `curl.exe -k https://wims.bfp.lan/health` (from second device) | `{"status":"ok",...}` | |

## 4. Clean data: no dev users, no demo incidents (exact SQL)

| # | SQL | Expected | Result |
|---|---|---|---|
| 4.1 | `sql "select username, role from wims.users order by 1"` | exactly **3** rows: `svc_suricata`, `svc_task`, and the bootstrap administrator | |
| 4.2 | `sql "select count(*) from wims.fire_incidents"` | 0 | |
| 4.3 | `sql "select (select count(*) from wims.incident_nonsensitive_details) a, (select count(*) from wims.analytics_incident_facts) b, (select count(*) from wims.data_import_batches) c, (select count(*) from wims.security_threat_logs) d, (select count(*) from wims.citizen_reports) e, (select count(*) from wims.security_threat_log_rollups) f"` | all 0 | |
| 4.4 | `sql "select count(*) from wims.users where username ~ '^(encoder_\|validator_test\|analyst\|admin_test\|[nger]-(val\|enc\|ana\|sys))'"` | 0 | |
| 4.5 | `sqlkc "select username from user_entity where realm_id = (select id from realm where name='bfp')"` | only the administrator | |
| 4.6 | Reference data present: `sql "select (select count(*) from wims.ref_regions) regions, (select count(*) from wims.ref_provinces) provinces, (select count(*) from wims.ref_cities) cities, (select count(*) from wims.ref_fire_stations) stations, (select count(*) from wims.system_config) config"` | regions 18; provinces, cities, stations, config all > 0 | |
| 4.7 | Real master key | `findstr WIMS_MASTER_KEY C:\WIMS\.env` | not `AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=`; 44 characters ending `=` | |
| 4.8 | No placeholder admin password | `findstr "admin" C:\WIMS\.env` | `KEYCLOAK_ADMIN='kcadmin'`; no `admin` password; `BOOTSTRAP_ADMIN_PASSWORD=''` after install | |

## 5. Bootstrap administrator: forced password change and OTP

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 5.1 | First login | https://wims.bfp.lan → sign in with the starting password | forced **Update password**; weak passwords and the old one rejected | |
| 5.2 | OTP enrolment | after the new password | QR code shown; app code accepted | |
| 5.3 | OTP required next time | sign out, sign in | password **and** 6-digit code asked | |
| 5.4 | Lands on admin | after login | `/admin/system` | |
| 5.5 | Keycloak admin works for the backend | Admin → System → create a user (role encoder, a region) | user created, listed (proves the backend's Keycloak admin login works after the temporary-admin profile step) | |
| 5.6 | Create validator, analyst, encoder | same page; use the temporary-password fallback for each (email will fail offline) | each can sign in and must change the password; validator must also enrol OTP; encoder/analyst need no OTP | |

## 6. Analytics policies (Phase 3b static check, now on a live database)

| # | SQL | Expected | Result |
|---|---|---|---|
| 6.1 | `sql "select policyname, cmd from pg_policies where schemaname='wims' and tablename='analytics_incident_facts' order by 1"` | 6 rows: `aif_national_analyst_read` SELECT, `aif_regional_read` SELECT, `aif_staff_delete` DELETE, `aif_staff_insert` INSERT, `aif_staff_update` UPDATE, `aif_validator_read` SELECT | |
| 6.2 | `sql "select privilege_type from information_schema.role_table_grants where table_schema='wims' and table_name='analytics_incident_facts' and grantee='wims_app' order by 1"` | DELETE, INSERT, SELECT, UPDATE | |
| 6.3 | `sql "select relrowsecurity, relforcerowsecurity from pg_class where oid='wims.analytics_incident_facts'::regclass"` | `t`, `t` | |

If 6.1 or 6.2 fail, **stop**: new incidents will not reach analytics. Record the output.

## 7. Phase 3b: incidents reach every analytics screen, without a manual sync

Create the data first: as **encoder** (own region) enter two incidents by *Manual Entry*
(one in the current quarter, one in an earlier quarter/year); as **admin** or encoder import one
real AFOR workbook (*Import AFOR* → commit). As **validator** approve all three.

| # | Check | Expected | Result |
|---|---|---|---|
| 7.1 | `sql "select incident_id, region_id, notification_date, general_category from wims.analytics_incident_facts order by 1"` | one row per **approved** incident (3 + the incidents inside the AFOR file); none for unapproved ones | |
| 7.2 | `docker compose logs backend celery-worker \| findstr /i "analytics sync"` | no "Analytics sync failed" / policy errors | |
| 7.3 | Do **not** call refresh-views. Open each analyst screen: Dashboard, Comparative, Heatmap, Trends, Response Time, Top-N Hotspots, Incident Explorer | every approved incident is reflected (counts, points, bars) | |
| 7.4 | Type distribution and response-time-by-region widgets | include the new incidents | |
| 7.5 | Year and quarter scoping | choose the year/quarter of each test incident: it appears there and not in others | |
| 7.6 | Variance figures (Comparative) | match a hand calculation from 7.1 (period A vs B) | |
| 7.7 | Exports as analyst: CSV, Excel, PDF, and the four workflow exports (comparative, trends, response time, top-N) | each completes, downloads, and contains the new incidents | |
| 7.8 | Unapproved/rejected incident | **not** in any screen; rejecting a verified one removes it | |
| 7.9 | Regional scoping | encoder sees only own region; analyst sees all | |

## 8. Role navigation: no 404s and no page errors

Open browser DevTools → Network (tick *Preserve log*). Sign in as each role and open **every**
sidebar entry. Expected for each: page renders, **no 404 or 5xx in Network**, no red error in
Console (offline-banner messages are fine).

| # | Role | Entries to open | Result |
|---|---|---|---|
| 8.1 | Encoder | Dashboard, Manual Entry, Import AFOR, Activity Log, Offline Work, My Profile | |
| 8.2 | Validator | Dashboard, Audit Trail, My Profile (+ open an incident and approve/reject/correct) | |
| 8.3 | Analyst | Analyst Dashboard, Comparative, Heatmap, Trends, Response Time, Top-N Hotspots, Incident Explorer, My Profile | |
| 8.4 | Admin | Admin Hub, Governance, Breach Notifications, Import AFOR, System Audit, Anomaly Detection, Configuration, Rate Limits, My Profile, Backups | |
| 8.5 | Each role lands on its own dashboard after login and never on another role's | | |

## 9. Removed URLs

Signed out (private window), each must end on `/login`; `/privacy` must load.

| # | URL | Expected | Result |
|---|---|---|---|
| 9.1 | `/`, `/register`, `/verify`, `/verify-sent`, `/report`, `/tracking/x`, `/fire-stations`, `/information`, `/community`, `/contributor`, `/incidents`, `/home` | redirect to `/login` | |
| 9.2 | `/privacy` | loads | |
| 9.3 | `https://wims.bfp.lan/api/civilian/reports`, `/api/triage/pending`, `/api/v1/public/report`, `/api/auth/register` | 404 (or 401 for authenticated-only), never a working civilian/public endpoint | |

## 10. Second device over HTTPS, and encoder offline create-and-sync

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 10.1 | No certificate warning | install CA (INSTALL §8) on the second device; open https://wims.bfp.lan in Edge/Chrome | padlock, no warning | |
| 10.2 | Without the CA | a third browser/device without the CA | warning shown (proves the CA is what makes it trusted) | |
| 10.3 | TLS 1.3 only | from the server: `docker run --rm --network host alpine/openssl s_client -connect wims.bfp.lan:443 -tls1_2` (needs a one-time pull; or use any TLS tester) | handshake **fails** for 1.2, succeeds for `-tls1_3` | |
| 10.4 | Headers | `curl.exe -skI https://wims.bfp.lan/login` | `Strict-Transport-Security`, CSP **without** `challenges.cloudflare.com`; no `Server` version | |
| 10.5 | HTTP redirects | `curl.exe -I http://wims.bfp.lan/login` | `301` to https | |
| 10.6 | Service worker | DevTools → Application → Service Workers | registered and active on https | |
| 10.7 | Offline create | sign in as encoder, load the dashboard once; DevTools *Offline* (or switch the device's Wi-Fi off); create an incident via Manual Entry | saved locally, "queued" indicator | |
| 10.8 | Sync | go back online | queue drains within ~1 min; incident visible in the encoder's list **and** for the validator (pending) | |
| 10.9 | Approved offline-created incident reaches analytics | validator approves | appears in analytics as in section 7 | |
| 10.10 | Offline reload | offline, reload the page | the app shell loads from cache | |

## 11. Breach form and the 30-second admin refresh

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 11.1 | Log a breach | Admin → Breach Notifications → *Log a breach* | saved; **deadline = detected time + 72 h** shown | |
| 11.2 | Audit row | `sql "select action_type, timestamp from wims.system_audit_trails where action_type like 'BREACH%' order by timestamp desc limit 3"` | a `BREACH_DETECTED` (or equivalent) row just now | |
| 11.3 | Row stored | `sql "select breach_id, status, detected_at, npc_deadline_at from wims.breach_notifications order by 1 desc limit 1"` | `DETECTED`, deadline 72 h after detected | |
| 11.4 | Email attempt | `docker compose logs backend celery-worker --tail 100 \| findstr /i "mail smtp"` | an attempt is logged; with no SMTP the failure is **logged, not a crash**, and the page still succeeds | |
| 11.5 | Status update | change the breach status | saved, audit row written | |
| 11.6 | Admin system page content | `/admin/system` | CPU, memory, disk and service health visible; no threat/AI/Suricata widgets | |
| 11.7 | 30-second refresh | DevTools → Network, filter `monitoring` / `health` / `metrics`, leave the page open 2 min | health + metrics + workers requests repeat every **30 s ± 2 s** | |

## 12. Backup, wipe everything, restore

Use test data from sections 5–10 (users with OTP, incidents with PII, an AFOR import, an uploaded file).

| # | Step | Expected | Result |
|---|---|---|---|
| 12.1 | Note counts: `sql "select (select count(*) from wims.fire_incidents), (select count(*) from wims.users)"`; open one incident with caller/owner names | write numbers and the names down | |
| 12.2 | `.\backup.ps1 -Destination E:\WIMS-Backups -SecretsDestination F:\WIMS-Secrets` | "Backup complete"; two folders; `manifest.json` has sizes and checksums | |
| 12.3 | Break test: edit one byte of `wims.dump` in a **copy** and run `restore.ps1` on it | refuses: "does not match its checksum" | |
| 12.4 | **Wipe** (test PC only): `docker compose down -v`; `Remove-Item .env -Force`; `Remove-Item certs -Recurse -Force`; `Remove-Item runtime -Recurse -Force`; restart the PC | no WIMS data left | |
| 12.5 | `.\restore.ps1 -BackupFolder … -SecretsFolder …` (type `RESTORE`) | images load, data restored, all containers healthy | |
| 12.6 | Counts and incidents | same numbers as 12.1 | |
| 12.7 | Encrypted PII readable | the incident from 12.1 shows the same names (proves the master key was restored) | |
| 12.8 | Logins survive | the administrator signs in with the **same** password and the **same** phone code; other users too | |
| 12.9 | Office PC still trusts the site | second device, without reinstalling the CA | no warning (same CA restored) | |
| 12.10 | Uploaded files | the file from the test is downloadable | |
| 12.11 | Daily schedule | `.\schedule-backup.ps1 …`; run the task from Task Scheduler | a new backup folder appears | |

## 13. Memory and load under a walkthrough

Run `docker stats --no-stream` (or Rancher's dashboard) at: (a) idle after boot; (b) during the
walkthrough – at the same time: an AFOR import, an Excel and a PDF export, and 3–4 browser
sessions; (c) after 1 hour idle. Compare with the **limit** (`MEM LIMIT` column).

| Service | Limit | Idle | Peak (walkthrough) | % of limit at peak | Result |
|---|---|---|---|---|---|
| postgres | 640 MiB | | | | |
| redis | 96 MiB | | | | |
| keycloak | 768 MiB | | | | |
| backend | 512 MiB | | | | |
| celery-worker | 640 MiB | | | | |
| frontend | 256 MiB | | | | |
| nginx | 64 MiB | | | | |
| **Total** | 2,976 MiB | | | | |

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 13.1 | No service killed for memory | `docker inspect -f "{{.Name}} OOMKilled={{.State.OOMKilled}} restarts={{.RestartCount}}" wims-postgres wims-redis wims-keycloak wims-backend wims-celery-worker wims-frontend wims-nginx` | all `OOMKilled=false`, `restarts=0` | |
| 13.2 | Headroom | every service ≤ 85 % of its limit at peak; if not, raise that service's `mem_limit` (and the WSL cap if needed) and record the new number | |
| 13.3 | Windows stays usable | Task Manager during the walkthrough | ≥ 2 GB free, no heavy paging | |
| 13.4 | Keycloak heap | `docker compose exec keycloak sh -c "ps aux \| grep -o 'Xmx[0-9a-z]*'"` | `Xmx448m` | |
| 13.5 | Response feel | dashboard and analytics screens | each loads in < 5 s on the LAN | |

## 14. Restart, power and update behaviour

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| 14.1 | Reboot | restart the PC, sign in to Windows, do nothing | https://wims.bfp.lan opens within ~5 min | |
| 14.2 | Power cut | switch off at the plug during use, power on | same as 14.1; no data loss beyond in-flight edits; Postgres recovers | |
| 14.3 | Never sleeps | leave the PC idle 1 h | still reachable | |
| 14.4 | Update bundle | build a second bundle (change anything trivial), copy over `C:\WIMS`, `.\install.ps1` | backup taken, new image loaded, data intact, `.env` and `certs\` untouched | |
| 14.5 | Internet down | with internet unplugged, create a user via the temporary-password fallback | works; the email failure does not block it | |

## 15. Sign-off

| Item | Name | Date | Signature |
|---|---|---|---|
| Tested by | | | |
| Result of sections 1–14 | all PASS / list of FAILs | | |
| Memory limits changed? (new values) | | | |
