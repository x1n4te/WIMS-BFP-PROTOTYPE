# Pre-Push Audit & Teammate Documentation Prompt

**Purpose:** Verify repository is safe to push to remote GitHub and ensure in-depth documentation exists for teammates.

**Target Agent:** Composer 1.5 (or equivalent code agent)

---

## Context Files (Read First)

Use `@` tags to load these files before execution:

- `@.gitignore` — Root ignore rules
- `@src/.gitignore` — Src-level ignore rules
- `@.specify/memory/constitution.md` — System architecture constraints
- `@.specify/memory/glossary.md` — Domain terminology
- `@src/docker-compose.yml` — Service definitions (check for secrets)

---

## Phase 1: Push Readiness Audit

### Step 1.1 — Git Status Verification

1. Run `git status` and capture output.
2. Run `git remote -v` and confirm `origin` points to the intended GitHub repository.
3. **Success criterion:** Output shows clean working tree OR explicitly lists staged/unstaged files. Remote URL is valid.

### Step 1.2 — Secrets & Sensitive Data Scan

1. Search the repository for patterns that MUST NOT be committed:
   - `.env`, `.env.local`, `.env.*.local`
   - `*.pem`, `*.key`
   - Hardcoded API keys, tokens, passwords (excluding dev-only placeholders in docker-compose)
2. Verify `.gitignore` and `src/.gitignore` exclude all sensitive paths.
3. **Negative constraint:** Do NOT modify `.env` or any file containing real secrets. Only report findings.
4. **Success criterion:** Produce a checklist: `[ ] No .env files tracked`, `[ ] No *.pem/*.key tracked`, `[ ] .gitignore covers secrets`.

### Step 1.3 — Ignored-But-Tracked Check

1. Run: `git ls-files --ignored --exclude-standard` (or equivalent).
2. If any ignored files are still tracked, list them.
3. **Success criterion:** Report: "No ignored files are tracked" OR list files that must be removed from git with `git rm --cached`.

### Step 1.4 — Binary & Large File Check

1. Identify files > 1MB that are tracked (excluding known assets like `*.xlsx` if intentional).
2. Check for binary blobs (e.g. `dump.rdb`, `*.pyc`) that should be ignored.
3. **Success criterion:** Report any large or binary files that should be added to `.gitignore`.

### Step 1.5 — Linter & Test Gate (Optional but Recommended)

1. Run backend tests: `cd src/backend && pytest -v` (or equivalent).
2. Run frontend tests if available: `cd src/frontend && npm test` (or `vitest run`).
3. **Success criterion:** Tests pass OR report failing tests that block a safe push.

---

## Phase 2: Teammate Documentation

### Step 2.1 — Create or Update CHANGELOG.md

**File:** `CHANGELOG.md` (repository root)

1. If `CHANGELOG.md` does not exist, create it.
2. Add a new `## [Unreleased]` section with:
   - **Changed:** List of modified modules/files and what changed (e.g. "`src/backend/api/routes/incidents.py` — Added triage endpoint").
   - **Added:** New features, endpoints, or components.
   - **Fixed:** Bug fixes.
   - **Security:** Any security-related changes.
3. Use `git diff --stat main` (or `master`) to infer changes if no prior changelog exists.
4. **Negative constraint:** Do NOT invent changes. Only document what `git diff` or `git log` shows.

### Step 2.2 — Create Architecture Overview

**File:** `docs/ARCHITECTURE.md` (create `docs/` if missing)

1. Document the system architecture:
   - **Stack:** Frontend (Next.js), Backend (FastAPI), DB (PostgreSQL/PostGIS), Auth (Keycloak), AI (Qwen2.5-3B).
   - **Key directories:** `src/frontend/`, `src/backend/`, `src/postgres-init/`, `src/supabase/`, `src/keycloak/`.
   - **Data flow:** Community Tier → Triage → Official Tier (reference `@.specify/memory/glossary.md`).
   - **Docker services:** List services from `docker-compose.yml` and their roles.
2. **Negative constraint:** Do NOT contradict `@.specify/memory/constitution.md`. Supabase is forbidden for auth.

### Step 2.3 — Create Function & API Reference

**File:** `docs/API_AND_FUNCTIONS.md`

1. Document backend API routes:
   - Read `src/backend/api/routes/*.py` and list endpoints with method, path, and brief description.
   - Read `src/backend/main.py` for app structure.
2. Document Supabase Edge Functions (if any):
   - List functions in `src/supabase/functions/` with purpose.
3. Document key frontend routes:
   - List pages under `src/frontend/src/app/` with purpose (e.g. `/incidents`, `/incidents/triage`, `/admin/system`).
4. **Success criterion:** Teammates can find "what endpoint does X" and "what page handles Y" without reading source.

### Step 2.4 — Update Root README.md

**File:** `README.md` (repository root)

1. If `README.md` exists, ensure it includes:
   - Project name (WIMS-BFP) and one-line description.
   - Links to `docs/ARCHITECTURE.md`, `docs/API_AND_FUNCTIONS.md`, `CHANGELOG.md`.
   - Prerequisites (Docker, Node, Python).
   - Quick start: `docker-compose up` or equivalent.
   - Where to find environment variables (e.g. `.env.example` if present).
2. If `README.md` does not exist, create it with the above sections.
3. **Negative constraint:** Do NOT overwrite `src/frontend/README.md`; that remains frontend-specific.

---

## Phase 3: Final Verification

### Step 3.1 — Documentation Completeness Checklist

Produce a final report:

```
## Pre-Push Audit Report
- [ ] Git status clean or explicitly documented
- [ ] No secrets/sensitive files tracked
- [ ] No ignored files incorrectly tracked
- [ ] No problematic large/binary files
- [ ] Tests pass (or failures documented)
- [ ] CHANGELOG.md created/updated
- [ ] docs/ARCHITECTURE.md created
- [ ] docs/API_AND_FUNCTIONS.md created
- [ ] README.md links to all docs
```

### Step 3.2 — Push Command (User Action)

After all checks pass, the agent must output:

```
Ready to push. Run:
  git add .
  git status   # Review staged files
  git commit -m "<your message>"
  git push origin <branch>
```

---

## Negative Constraints (Strict)

- **Do NOT** modify `.env`, `*.pem`, `*.key`, or any file containing real credentials.
- **Do NOT** remove or alter `.gitignore` entries for secrets.
- **Do NOT** change `src/frontend/README.md` beyond adding a link to root docs.
- **Do NOT** contradict `.specify/memory/constitution.md` (e.g. do not document Supabase as auth provider).
- **Do NOT** run `git push` automatically; only output the command for the user to run.

---

## Success State (Deterministic)

The task is **done** when:

1. The Pre-Push Audit Report shows all checkboxes either satisfied or explicitly documented as N/A.
2. `CHANGELOG.md`, `docs/ARCHITECTURE.md`, and `docs/API_AND_FUNCTIONS.md` exist and contain non-empty, accurate content.
3. `README.md` links to the new documentation.
4. The agent outputs the exact `git push` command for the user to execute manually.
