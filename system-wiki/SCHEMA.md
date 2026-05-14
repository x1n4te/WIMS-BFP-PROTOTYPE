# System Wiki Schema

## Domain
This project-local system wiki documents WIMS-BFP as implemented in this repository: FastAPI backend, Next.js frontend, PostgreSQL/PostGIS schema, Keycloak authentication, Suricata/XAI security monitoring, and the current FRS-to-code alignment state.

This is a builder-agent routing knowledgebase. It is not the thesis paper wiki and not a user manual.

## Authority Model
1. Raw FRS files in `raw/frs/` are product-requirement sources supplied by the user for this initialization.
2. Live repository files under `src/` are implementation evidence.
3. Pages in this wiki are downstream synthesis and must cite source paths.
4. If FRS and code disagree, record the discrepancy in `gaps/` instead of silently rewriting either side.
5. Empty or incomplete FRS source files are treated as knowledge gaps, not as evidence that the module has no requirements.

## Conventions
- File names: lowercase, hyphenated, no spaces.
- Every synthesis page starts with YAML frontmatter.
- Use Obsidian-style double-bracket links for navigability; each page should link to at least two other pages.
- Use repository paths in backticks for implementation references.
- `raw/` is immutable; do not edit raw source captures except by replacing from a newer authoritative source batch.
- Update `index.md` and `log.md` for every wiki change.
- `system-wiki/` is project-local and may be committed if the team wants agent context in Git.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: schema | moc | concept | architecture | backend | frontend | database | security | operations | gap | raw-index | ui-ux
tags: [from taxonomy below]
sources: [raw/frs/source.md, src/path]
status: draft | verified | needs-review
---
```

## Tag Taxonomy
- core: `wims-bfp`, `system-wiki`, `agent-routing`, `frs`, `codebase`
- layers: `frontend`, `backend`, `database`, `keycloak`, `suricata`, `nginx`, `redis`, `celery`, `docker`
- domains: `auth`, `incident-management`, `offline-first`, `triage`, `immutability`, `analytics`, `crypto`, `ids`, `xai`, `monitoring`, `compliance`, `pentest`, `users`, `notifications`, `public-dmz`, `reference-data`, `ui-ux`, `hci`
- security: `security`, `rbac`, `rls`, `audit-log`, `privacy`, `fail-closed`
- meta: `gap`, `needs-verification`, `implementation-map`, `source-index`

## Page Thresholds
- Create pages for stable architectural layers, FRS modules, major routes, database schema groups, and agent-routing guidance.
- Do not create a page for a tiny helper unless it carries security or architectural risk.
- Split pages over ~200 lines.

## Update Policy
When Agile development changes a feature:
1. Update the raw source only if a new authoritative FRS/source file is supplied.
2. Update synthesis pages with the new implementation facts.
3. Add or update the relevant gap entry if implementation moved ahead of the FRS or diverged from it.
4. Preserve provenance by citing exact source paths.
