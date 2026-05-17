# WIMS-BFP — QA Dogfood Report

**Test Date:** 2026-05-17
**Tester:** Ares (Hermes Agent)
**Scope:** Authenticated UX walkthrough — NATIONAL_ANALYST role (also revisiting REGIONAL_ENCODER findings)
**Environment:** Docker stack (localhost), branch `dev/dev-bypass-auth`
**Auth:** `POST /api/dev-login` with `qa_auto` (Keycloak role: REGIONAL_ENCODER + NATIONAL_ANALYST; DB role: NATIONAL_ANALYST after manual update)
**Note:** `qa_auto`'s Keycloak roles were updated mid-session to include NATIONAL_ANALYST. The `wims.users` DB role was manually updated from REGIONAL_ENCODER to NATIONAL_ANALYST to match. The Keycloak direct grant produces a token with `realm_access.roles` containing both roles — but `get_current_wims_user` resolves from `wims.users` DB, so the effective role is whatever is in the DB.

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Issues | 10 |
| Critical | 0 |
| High | 1 |
| Medium | 5 |
| Low | 4 |

### Issue Breakdown by Category

| Category | Count |
|----------|-------|
| Functional | 4 |
| Visual | 1 |
| Accessibility | 1 |
| Console | 1 |
| UX | 3 |
| Content | 1 |

---

## Phase 1: REGIONAL_ENCODER Walkthrough

**Method:** `POST /api/dev-login` — Keycloak direct grant bypass (branch `dev/dev-bypass-auth`)

```js
// Browser console
fetch('/api/dev-login', {
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body: JSON.stringify({role:'REGIONAL_ENCODER', username:'qa_auto', password:'QaAuto2026!Aa'})
}).then(r=>r.json()).then(d=> {
  document.cookie='access_token='+d.access_token+'; path=/; domain=localhost';
})
```

Result: Authenticated successfully. Dashboard shows `qa_auto@bfp.gov.ph` as `REGIONAL_ENCODER`.

**Note:** The `Auto-fill (Test)` button on Manual AFOR Entry navigates away from the authenticated zone (lands on `/login`). This is a destructive session-loss issue — see ISSUE-3.

---

## Issues

### ISSUE-1: Change Password form incorrectly requires TOTP (High)

**Severity:** High
**Category:** UX
**URL:** `/profile` → Change Password section
**Reported by:** Ares

#### Description

The "Change Password" section on the My Profile page shows a `textbox "6-digit code from your authenticator app"` (TOTP field). This field is part of the Keycloak password change flow, but the local password change UI should not require TOTP to change your own password. The field is visible and labeled, but the user (`qa_auto`) has no TOTP device enrolled in Keycloak, making this flow impossible to complete.

#### Steps to Reproduce
1. Navigate to `/profile`
2. Scroll to "Change Password"
3. Observe the `6-digit code from your authenticator app` textbox

#### Expected Behavior
Local password change should only require: current password + new password + confirm. No TOTP.

#### Actual Behavior
A TOTP input field is displayed. Change Password button remains disabled until all 4 fields are filled.

---

### ISSUE-2: Date/Time spinbuttons default to zero, not today's date (Medium)

**Severity:** Medium
**Category:** Functional
**URL:** `/dashboard` (Filters → DATE FROM/TO), `/afor/create` (all date/time fields)
**Reported by:** Ares

#### Description

On the Dashboard filter, the DATE FROM and DATE TO spinbuttons show `Month: 0, Day: 0, Year: 0` instead of pre-populating with today's date. The same pattern appears in all date/time fields on the Manual AFOR Entry page. The placeholder text shows `mm/dd/yyyy` and `—:—— —M` but the actual input values are `0`.

A user must manually type or select every date component. This adds friction for the primary use case (filtering today's or recent incidents).

#### Steps to Reproduce
1. Go to `/dashboard`
2. Look at DATE FROM spinbuttons — values are `0, 0, 0`

#### Expected Behavior
DATE FROM should default to 7 days ago; DATE TO should default to today.

#### Actual Behavior
All date/time spinbuttons initialize to `0` / `--`.

---

### ISSUE-3: "Auto-fill (Test)" button loses authentication session (Medium)

**Severity:** Medium
**Category:** Functional
**URL:** `/afor/create`
**Reported by:** Ares

#### Description

Clicking the "Auto-fill (Test)" button on the Manual AFOR Entry page navigates the browser to `/login`, losing the authenticated session. The button appears to be wired to a Keycloak OIDC redirect rather than a local `fetch()` auto-fill function.

This was observed during testing when `browser_click(ref="e4")` (Auto-fill button) redirected to the login page.

#### Steps to Reproduce
1. Navigate to `/afor/create`
2. Click "Auto-fill (Test)"
3. Observe redirect to `/login` — session cookie is lost

#### Expected Behavior
Auto-fill should populate form fields with test data client-side without navigation.

#### Actual Behavior
Full page redirect to `/login`.

---

### ISSUE-4: Account Information section has missing field labels (Medium)

**Severity:** Medium
**Category:** Content
**URL:** `/profile` → Account Information
**Reported by:** Ares

#### Description

The "Account Information" section shows empty paragraphs between "Account Information" and "Regional Encoder". The user email, username, and user_id fields are not labeled — they appear as blank paragraphs followed by the role display.

From the snapshot:
```
- generic "Account Information"
- paragraph (empty)
- paragraph (empty)
- paragraph (empty)
- StaticText "Regional Encoder"
- paragraph (empty)
...
```

The actual data (email: `qa_auto@bfp.gov.ph`, username: `qa_auto`) is returned by the API but labels are missing in the UI.

#### Steps to Reproduce
1. Navigate to `/profile`
2. Look at the Account Information section

#### Expected Behavior
Each field should have a label: Email, Username, User ID.

#### Actual Behavior
Fields render as unlabeled blank lines followed by the role.

---

### ISSUE-5: Dashboard stat cards missing labels (Low)

**Severity:** Low
**Category:** Accessibility
**URL:** `/dashboard`
**Reported by:** Ares

#### Description

The three generic clickable stat cards (`ref=e18, e19, e20`) adjacent to "TOTAL FIRE INCIDENTS 12" have no accessible labels. They appear visually as stat cards but have no `aria-label`, no visible text, and no `title` attribute. A screen reader user would encounter three unlabeled interactive elements.

#### Steps to Reproduce
1. Go to `/dashboard`
2. Inspect the stat card elements — `ref=e18, e19, e20` are `generic [clickable]` with no accessible name

#### Expected Behavior
Each card should have an `aria-label` or visible text describing what metric it shows.

#### Actual Behavior
Empty generic elements with `cursor:pointer` but no accessible name.

---

### ISSUE-6: Current password field shows "—" instead of masked placeholder (Low)

**Severity:** Low
**Category:** Visual
**URL:** `/profile` → Change Password
**Reported by:** Ares

#### Description

The "Current password" row shows `StaticText "—" ` as the placeholder/mask instead of bullet characters (`••••••••`). When no current password is entered, the mask should be bullets to communicate "enter your current password."

#### Steps to Reproduce
1. Go to `/profile` → Change Password
2. Look at the current password field — shows `—`

#### Expected Behavior
Should show `••••••••` or empty with `Enter current password` placeholder text.

#### Actual Behavior
Shows `—` as a static placeholder character.

---

## Phase 2: NATIONAL_ANALYST Walkthrough

### Analyst Navigation Structure

The NATIONAL_ANALYST role exposes a dedicated analyst sidebar with 8 sub-pages:

| Page | Route | Status |
|------|-------|--------|
| Analyst Dashboard | `/dashboard` | Working — "Configuration Required" banner, stat cards (0 VISIBLE INCIDENTS, 0 ACTIVE FILTERS), comparative period dates pre-populated |
| Comparative | `/dashboard` (nav) | Working — Range A (Apr 17 – May 2) and Range B (May 3 – May 17) pre-populated; shows 0/0/0 variance (no data in those ranges) |
| Heatmap | `/dashboard` (nav) | Working — Leaflet map with 12 mapped incidents from seed data; "Refresh workflow" button; filter panel + incident table |
| Trends | `/dashboard` (nav) | Working — Time series bar chart, 12 incidents from Jan–Mar 2026; PEAK BUCKET Jan 8; daily/weekly/monthly/quarterly/yearly interval selector |
| Response Time | `/dashboard` (nav) | Working — Bar chart, MEAN REGIONAL AVG 46.0 min, FASTEST 18.0 min, SLOWEST 96.0 min; grouped by region (NCR, Region V, Region IV-A) |
| Top-N Hotspots | `/dashboard` (nav) | Working — Ranked table, 10 municipalities; metric (Incidents/Response Time/Casualties) and dimension (Municipality/Barangay/Fire Station/Region) selectors |
| Incident Explorer | `/dashboard` (nav) | Working — Sortable table with 12 seed incidents; columns: Notification, Region, Municipality, Barangay, Category, Sub Category, Alarm, Damage, Response |
| My Profile | `/profile` | Working — Same TOTP and label issues as REGIONAL_ENCODER |

### Analyst-Specific Issues

### ISSUE-7: Analyst Dashboard shows "Configuration Required" banner (Medium)

**Severity:** Medium
**Category:** UX
**URL:** `/dashboard` (NATIONAL_ANALYST)
**Reported by:** Ares

#### Description

Even as NATIONAL_ANALYST (which has no region assignment in the FRS — national scope), the dashboard shows a red "Configuration Required" banner: "No region assigned to your account. Contact your administrator."

For a NATIONAL_ANALYST, having no region is the expected, correct state. The banner should not appear for this role.

#### Steps to Reproduce
1. Authenticate as NATIONAL_ANALYST
2. Navigate to `/dashboard`
3. Observe "Configuration Required" banner

#### Expected Behavior
No banner for NATIONAL_ANALYST — a national analyst legitimately has no region.

#### Actual Behavior
Red configuration banner visible regardless of role.

---

### ISSUE-8: Comparative page shows 0/0 variance when seeded data is Jan–Mar (Medium)

**Severity:** Medium
**Category:** Functional
**URL:** `/dashboard` (Comparative view)
**Reported by:** Ares

#### Description

The Comparative view pre-populates two date ranges: Range A (Apr 17 – May 2) and Range B (May 3 – May 17). However, all 12 seeded incidents occurred in January–March 2026. This means both ranges show `0` incidents, `+0%` variance, and the evidence table is empty.

A user looking at the page for the first time sees an interface that appears broken (no data, 0%) rather than informative.

#### Steps to Reproduce
1. Authenticate as NATIONAL_ANALYST
2. Navigate to Comparative
3. Observe Range A: 0, Range B: 0, Variance: +0%

#### Expected Behavior
Either the comparative ranges should default to ranges that overlap with existing data, or a message should explain "No incidents found in selected periods."

#### Actual Behavior
Pre-populated date ranges have no overlap with seed data, creating a misleading empty-state appearance.

---

### ISSUE-9: Console errors — refreshAccessToken: 401 (Low)

**Severity:** Low
**Category:** Console
**URL:** Multiple (observed on Profile page)
**Reported by:** Ares

#### Description

Browser console shows repeated errors:
```
[AuthContext] refreshAccessToken: refresh failed 401
```

This indicates the token refresh mechanism is failing. The dev-bypass token may have no refresh token configured, or the refresh endpoint is not accessible.

#### Steps to Reproduce
1. Authenticate via `/api/dev-login`
2. Navigate to `/profile`
3. Open browser console — observe `refreshAccessToken: refresh failed 401`

#### Expected Behavior
No 401 errors on refresh — token refresh should work or the system should handle refresh failure gracefully (redirect to login).

#### Actual Behavior
Repeated 401 errors on token refresh attempts.

---

### ISSUE-10: Analyst heatmap shows no data when default filters applied (Low)

**Severity:** Low
**Category:** Functional
**URL:** `/dashboard` (Heatmap)
**Reported by:** Ares

#### Description

The heatmap shows "MAPPED INCIDENTS: 12" (good) and the incident table below shows "12 total" (good). However, the filter panel shows all date spinbuttons at `0` — meaning the map is showing unfiltered data while the filter panel shows no filters active. This inconsistency could confuse analysts who expect the map to honor the filter state.

#### Steps to Reproduce
1. Navigate to Heatmap as NATIONAL_ANALYST
2. Observe "MAPPED INCIDENTS: 12" (correct — all seed incidents)
3. Look at filter spinbuttons — all `0, 0, 0`
4. Click "Apply" without changing anything — the result is the same

#### Expected Behavior
Either the map should show 0 incidents (because date filters default to 0 = no date range), or the filter display should show "No date filter" clearly.

#### Actual Behavior
The map displays all 12 incidents despite filter spinbuttons showing `0, 0, 0`.

---

## Summary Table

| # | Title | Severity | Category | Status |
|---|-------|----------|----------|--------|
| 1 | Change Password requires TOTP (user has no TOTP device) | High | UX | Open |
| 2 | Date/time spinbuttons default to zero, not today | Medium | Functional | Open |
| 3 | Auto-fill button navigates away and loses session | Medium | Functional | Open |
| 4 | Account Information fields missing labels | Medium | Content | Open |
| 5 | Stat cards have no accessible labels | Low | Accessibility | Open |
| 6 | Current password placeholder shows "—" instead of bullets | Low | Visual | Open |
| 7 | "Configuration Required" banner shown to NATIONAL_ANALYST (no region is correct for this role) | Medium | UX | Open |
| 8 | Comparative pre-populated date ranges (Apr–May) have zero overlap with Jan–Mar seed data | Medium | Functional | Open |
| 9 | `refreshAccessToken: refresh failed 401` console errors after auth | Low | Console | Open |
| 10 | Heatmap shows 12 incidents despite filter spinbuttons at 0/0/0 | Low | Functional | Open |

---

## Testing Notes

**Auth method:** `POST /api/dev-login` bypass (branch `dev/dev-bypass-auth`). Cookie injected via browser console.

**REGIONAL_ENCODER tested:**
- `/` — Landing/login page (LOGIN WITH KEYCLOAK button)
- `/dashboard` — Dashboard with filters, stat cards, date pickers
- `/afor/create` — Manual AFOR Entry (Structural path, all form sections)
- `/afor/import` — Regional AFOR Import (upload UI, template links)
- `/profile` — My Profile (account info, edit profile, change password)
- `/api/auth/session` — Session endpoint with valid cookie → correct user data
- `/api/dev-login` — Dev bypass endpoint → returns access_token + refresh_token

**NATIONAL_ANALYST tested:**
- `/dashboard` — Analyst Dashboard (stat cards, workflow links, comparative period selectors)
- `/dashboard` (Comparative) — Range A/B variance comparison
- `/dashboard` (Heatmap) — Leaflet map, incident evidence table
- `/dashboard` (Trends) — Time series bar chart, interval selector
- `/dashboard` (Response Time) — Regional bar chart, min/avg/max response times
- `/dashboard` (Top-N Hotspots) — Ranked municipality table with metric/dimension selectors
- `/dashboard` (Incident Explorer) — Sortable data table with 12 seed incidents
- `/profile` — My Profile (same TOTP/label issues as REGIONAL_ENCODER)
- API endpoints: `/api/analytics/heatmap`, `/api/analytics/trends`, `/api/analytics/top-n`, `/api/analytics/response-time-by-region`, `/api/analytics/compare-regions`

**Not Tested:**
- Form submission (AFOR submit, profile save)
- Province/City cascading (requires region to be selected first)
- Import AFOR file upload (requires actual .xlsx file)
- Sign out flow
- NATIONAL_VALIDATOR and SYSTEM_ADMIN roles
- Civilian reporting flow (separate unauthenticated path)
- TOTP enrollment flow

**Auth note:** Cookie injection via `document.cookie='access_token=...'` on `/login` page is blocked (SecurityError on `/login`). Must navigate to an authenticated page first, then inject cookie. Workaround: inject cookie on an API endpoint page (`/api/dev-login`) then navigate to protected pages.

**Key root cause found during analyst testing:** `qa_auto` had REGIONAL_ENCODER in `wims.users` but was assigned NATIONAL_ANALYST in Keycloak. `get_current_wims_user` resolves role from the DB, not from the JWT. The dev-bypass endpoint accepts any `role` parameter but only uses it to set the Keycloak direct grant — the actual role in the app is determined by the `wims.users` table. Had to manually update `wims.users.role = 'NATIONAL_ANALYST'` and add the Keycloak role via Keycloak Admin API.

**Blockers:**
- TOTP required on local password change — no workaround for users without TOTP device enrolled in Keycloak
- Auto-fill button navigates to `/login` — loses session
- `analyst_test` and `analyst1_test` Keycloak accounts existed but had no working password — could not use dev-login with those accounts
- Seed data (Jan–Mar 2026) does not overlap with pre-populated comparative date ranges (Apr–May 2026) — causes 0/0 variance on first load

---

*Report generated by Hermes Agent dogfood QA skill.*