# Pre-Push Audit & Docs Update Prompt
**Purpose:** Audit the repository for push safety and update teammate-facing documentation with accurate, source-grounded changes only.
**Target Agent:** Composer 1.5 or equivalent code agent
---
## Read Targets First
Load these files before taking any action:
- `@.gitignore`
- `@src/.gitignore`
- `@.specify/memory/constitution.md`
- `@.specify/memory/glossary.md`
- `@src/docker-compose.yml`
- `@README.md`
- `@src/backend/main.py`
If any of the following exist, read them before editing:
- `@CHANGELOG.md`
- `@docs/ARCHITECTURE.md`
- `@docs/API_AND_FUNCTIONS.md`
Also inspect these directories if they exist:
- `@src/backend/api/routes/`
- `@src/frontend/src/app/`
- `@src/supabase/functions/`
- `@src/postgres-init/`
- `@src/keycloak/`
---
## Write Targets
You may create or update only these files:
- `CHANGELOG.md`
- `docs/ARCHITECTURE.md`
- `docs/API_AND_FUNCTIONS.md`
- `README.md`
Do not modify any other tracked file unless the final report explicitly explains why it was necessary and the file is one of the four targets above.
---
## Phase 0: Red-State Validation
Before making changes, produce a brief red-state findings list based on actual repository evidence.
### Step 0.1 - Validate Required Inputs
1. Confirm which of the read-target files exist.
2. If any required file is missing, note it explicitly and continue only if the task can still be completed safely.
3. Do not guess file contents.
### Step 0.2 - Validate Current Documentation State
1. Check whether `CHANGELOG.md`, `docs/ARCHITECTURE.md`, `docs/API_AND_FUNCTIONS.md`, and `README.md` already exist.
2. For each existing file, identify gaps, stale sections, or missing links.
3. For each missing file, mark it for creation.
### Step 0.3 - Validate Push-Readiness Risks
1. Run `git status` and capture the result.
2. Run `git remote -v` and confirm `origin` is configured.
3. Identify whether the working tree is clean, dirty, or partially staged.
4. Report these findings before editing documentation.
---
## Phase 1: Push Readiness Audit
### Step 1.1 - Git Status Verification
1. Run `git status`.
2. Run `git remote -v`.
3. Report:
   - branch name
   - whether the working tree is clean
   - whether untracked, staged, or unstaged files exist
   - whether `origin` is present
**Success criterion:** Git state is explicitly documented with no ambiguity.
### Step 1.2 - Secrets and Sensitive Data Scan
1. Check for tracked or staged files matching:
   - `.env`
   - `.env.local`
   - `.env.*.local`
   - `*.pem`
   - `*.key`
2. Check for hardcoded secrets or credentials in tracked files, excluding obvious placeholders used only for local development.
3. Verify `.gitignore` and `src/.gitignore` cover secret-bearing paths where appropriate.
4. Report findings as a checklist.
**Success criterion:**
- `[ ] No .env files tracked`
- `[ ] No .pem or .key files tracked`
- `[ ] No real credentials found in tracked files`
- `[ ] Ignore rules cover sensitive paths`
### Step 1.3 - Ignored-But-Tracked File Check
1. Detect files that are ignored by current ignore rules but still tracked by git.
2. List each such file if found.
3. If none are found, state that explicitly.
**Success criterion:** Report either `No ignored files are tracked` or a precise list of offending files.
### Step 1.4 - Large and Binary File Check
1. Identify tracked files larger than 1 MB.
2. Identify binary or generated files that should likely not be versioned, such as caches, dumps, compiled artifacts, or machine-specific files.
3. Exclude intentional assets only if the repo structure clearly supports them.
**Success criterion:** Report either `No problematic large/binary tracked files found` or a precise list of concerns.
### Step 1.5 - Test and Lint Gate
1. Run backend tests if the backend test runner is present.
2. Run frontend tests if a frontend test runner is present.
3. If a linter is clearly configured and cheap to run, run it.
4. If a test or lint command is unavailable, state that explicitly instead of inventing a substitute.
**Success criterion:** Report passing commands, failing commands, or unavailable commands with exact outcomes.
---
## Phase 2: Documentation Update
### Step 2.1 - Update `CHANGELOG.md`
1. Create `CHANGELOG.md` if it does not exist.
2. Add or update a `## [Unreleased]` section.
3. Populate only with changes supported by repository evidence from:
   - `git diff`
   - `git diff --stat`
   - `git log`
   - actual file inspection
4. Use these headings when applicable:
   - `### Added`
   - `### Changed`
   - `### Fixed`
   - `### Security`
5. Do not invent features, fixes, or refactors.
**Success criterion:** `CHANGELOG.md` contains an accurate unreleased section grounded in visible repo changes.
### Step 2.2 - Create or Update `docs/ARCHITECTURE.md`
1. Create `docs/` if needed.
2. Document the actual system architecture using repository evidence.
3. Include:
   - stack summary
   - key directories and their roles
   - service overview from `src/docker-compose.yml`
   - high-level data flow using `@.specify/memory/glossary.md` where relevant
4. Respect `@.specify/memory/constitution.md` exactly.
5. If a technology is not clearly present in the repo, do not present it as fact.
**Success criterion:** `docs/ARCHITECTURE.md` gives a teammate a truthful high-level map of the system.
### Step 2.3 - Create or Update `docs/API_AND_FUNCTIONS.md`
1. Document backend routes from `src/backend/api/routes/` if present.
2. Read `src/backend/main.py` to understand app entry and mounting structure.
3. Document:
   - HTTP method
   - route path
   - short purpose
4. If `src/supabase/functions/` exists, list each function and its purpose.
5. If `src/frontend/src/app/` exists, list key frontend routes/pages and their purpose.
6. Only include endpoints and pages you can verify from source.
**Success criterion:** A teammate can locate the main APIs and user-facing routes without reading the code first.
### Step 2.4 - Update `README.md`
1. Ensure `README.md` includes:
   - project name and one-line description
   - links to `CHANGELOG.md`, `docs/ARCHITECTURE.md`, and `docs/API_AND_FUNCTIONS.md`
   - basic setup or quick-start information if already supported by repo evidence
   - references to environment setup if such documentation already exists
2. Preserve existing valid content where possible.
3. Prefer additive edits over destructive rewrites.
**Success criterion:** Root `README.md` links to the generated documentation and remains accurate.
---
## Phase 3: Green-State Verification
### Step 3.1 - Verify Documentation Accuracy
1. Re-read the updated `CHANGELOG.md`, `docs/ARCHITECTURE.md`, `docs/API_AND_FUNCTIONS.md`, and `README.md`.
2. Confirm that every substantive statement is supported by repository evidence.
3. Remove any guessed or weakly supported claims.
### Step 3.2 - Verify Scope Control
1. Confirm that only the allowed write targets were modified.
2. If any other file was changed, stop and report it clearly.
### Step 3.3 - Produce Final Report
Output this exact structure:
```text
## Pre-Push Audit Report
- [ ] Git status documented
- [ ] Remote documented
- [ ] No tracked secret files found, or findings explicitly listed
- [ ] No ignored-but-tracked files found, or findings explicitly listed
- [ ] No problematic large/binary tracked files found, or findings explicitly listed
- [ ] Tests/lint run or marked unavailable with exact outcomes
- [ ] CHANGELOG.md created or updated
- [ ] docs/ARCHITECTURE.md created or updated
- [ ] docs/API_AND_FUNCTIONS.md created or updated
- [ ] README.md updated to link docs
## Files Modified
- CHANGELOG.md
- docs/ARCHITECTURE.md
- docs/API_AND_FUNCTIONS.md
- README.md
## Notes
- <brief factual notes only>
Ready to push. Run:
  git add .
  git status
  git commit -m "<your message>"
  git push origin <branch>
Strict Negative Constraints
Do not modify .env, .env.*, *.pem, *.key, or any file containing real credentials.
Do not remove or weaken ignore rules for secret files.
Do not run git push.
Do not fabricate test results, architecture details, routes, pages, or changelog entries.
Do not document Supabase as the auth provider if @.specify/memory/constitution.md forbids it.
Do not overwrite README.md unnecessarily when a targeted edit is sufficient.
Do not modify src/frontend/README.md unless it is explicitly one of the allowed write targets, which it is not.
Do not edit files outside:
CHANGELOG.md
docs/ARCHITECTURE.md
docs/API_AND_FUNCTIONS.md
README.md
Deterministic Definition of Done
The task is done only when all of the following are true:

The git audit findings are explicitly reported.
Documentation changes are limited to the four allowed write targets.
CHANGELOG.md, docs/ARCHITECTURE.md, and docs/API_AND_FUNCTIONS.md exist and contain non-empty, source-grounded content.
README.md links to the documentation files.
The final report uses the required checklist format.
The agent outputs the manual push command and does not execute it.