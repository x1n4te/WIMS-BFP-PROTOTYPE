# Repository Guidelines

## Project Structure & Module Organization

This repository is a Dockerized WIMS-BFP full-stack prototype. Primary implementation lives in `src/`: `src/backend/` contains the FastAPI API, Celery tasks, models, schemas, and pytest tests; `src/frontend/` contains the Next.js App Router application, React components, client libraries, public assets, and Vitest tests. Database bootstrap SQL is in `src/postgres-init/`. Keycloak files are in `src/keycloak/`, Nginx config is in `src/nginx/`, and Suricata rules/log mounts are in `src/suricata/`. Project notes live in `docs/`; seed and utility scripts live in `scripts/`.

## Build, Test, and Development Commands

- `cd src && docker compose up --build`: build and run the local stack.
- `cd src && docker compose down`: stop the local stack without deleting volumes.
- `cd src/backend && pytest -v`: run backend unit and integration tests from `src/backend/tests`.
- `cd src/frontend && npm run dev`: start the Next.js dev server.
- `cd src/frontend && npm run build`: create a production frontend build.
- `cd src/frontend && npm run lint`: run ESLint.
- `cd src/frontend && npx vitest run`: run frontend tests.

Install frontend dependencies with `npm install` in `src/frontend/`. For non-Docker backend work, install `src/backend/requirements.txt` in a Python 3.10+ virtual environment.

## Coding Style & Naming Conventions

Use Python 3.10+ style in the backend: 4-space indentation, typed FastAPI route signatures where practical, `snake_case` for functions/modules, and explicit Pydantic schemas in `schemas/`. Keep routes grouped by domain under `src/backend/api/routes/`.

Frontend code is TypeScript/React. Use `PascalCase` for components, `camelCase` for functions and variables, and colocate tests beside code. Follow existing ESLint and Next.js conventions; avoid broad formatting churn.

## Testing Guidelines

Backend pytest discovery is configured in `src/backend/pytest.ini` with `testpaths = tests`. Name tests `test_*.py`; place integration-heavy cases under `src/backend/tests/integration/`. Frontend tests use Vitest, React Testing Library, and jsdom; name files `*.test.ts` or `*.test.tsx`. Run relevant tests before opening a PR.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style subjects, often with issue references, such as `feat(#46): ...`, `fix(auth): ...`, and `style: ...`. Keep subjects imperative and scoped when useful.

Pull requests should include a short problem/solution summary, linked issues, test results, and screenshots for visible UI changes. Call out schema, auth, environment, or data-volume impacts explicitly. Never commit real secrets; Docker Compose values are development defaults only.
