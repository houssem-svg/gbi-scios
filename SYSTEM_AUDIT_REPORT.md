# GBI-SCIOS Full System Stabilization Audit

Date: 2026-06-16

## Executive Status

The MVP is now runnable end-to-end for an enterprise pilot simulation. A root-launched Uvicorn smoke test completed:

- register/login token path
- project creation
- mandatory list upload
- BoQ upload
- BoQ parsing
- compliance scan
- dashboard summary
- report generation
- PDF download

Verification result:

```text
root_e2e ok ... mandatory=1 parse=1 violations=1 dashboard_projects=1 report=COMPLETED pdf_bytes=53708
```

Frontend production build also passes with Next.js.

## Critical Issues

1. Frontend forced trailing slashes on API calls.

Root cause: `lib/api.ts` appended `/` to every endpoint while FastAPI routes were registered without trailing slashes. This caused 307 redirects and could drop `Authorization` headers, producing authenticated workflow failures.

Repair: `gbi-scios-frontend/lib/api.ts` now preserves canonical endpoint paths. `gbi-scios-frontend/lib/uploadService.ts` was also corrected from `/uploads/` to `/uploads`.

2. Reporting model used integer foreign keys for UUID tables.

Root cause: `Report.project_id` and `Report.generated_by` were declared as `Integer`, while `projects.id` and `users.id` are UUID columns. SQLite tolerated bad values, but SQLAlchemy/Postgres contracts were invalid.

Repair: `Report` model, reporting schema, reporting service, and Alembic reports migration now use UUID-compatible columns and serialization.

3. Existing SQLite database had already-applied bad reports schema.

Root cause: Alembic was marked at head while the local `reports` table still had integer columns.

Repair: local `reports` table was rebuilt with `char(32)` UUID storage and seven existing report rows were preserved with normalized UUID values.

4. Launch directory changed backend behavior.

Root cause: a stale top-level `app` package could shadow the real backend package, and backend settings loaded `.env` relative to current working directory.

Repair: top-level `app` now delegates to the real backend package, and backend config resolves `.env`, SQLite DB, upload logs, parsing logs, and compliance logs relative to the backend root.

## High Issues

1. Frontend report contract was still mock-era.

Root cause: frontend expected `title`, `risk_score`, `generated_at`, and `compliance_metrics`; backend returns `report_type`, `status`, `json_payload`, `created_at`, and `file_path`.

Repair: report types, report service, report card, and reports page now map to the backend response.

2. Report PDF storage was current-directory dependent.

Root cause: report generation used `./storage/reports`, which changes depending on where Uvicorn is launched.

Repair: report storage and download validation now resolve under the backend root.

3. PDF dependencies were missing from backend project metadata.

Root cause: `reporting.py` and `pdf_helpers.py` import ReportLab, Arabic reshaping, and bidi helpers, but `pyproject.toml` did not declare them.

Repair: `pyproject.toml` now declares `reportlab`, `arabic-reshaper`, and `python-bidi`.

## Medium Issues

1. FastAPI `TestClient` is blocked locally by dependency drift.

Root cause: installed Starlette expects `httpx2`; the local venv does not include it. Runtime API behavior was verified with real Uvicorn instead.

Status: documented residual tooling issue. MVP runtime is not blocked.

2. Next.js warns that `middleware.ts` convention is deprecated.

Root cause: Next.js 16 prefers the newer proxy convention.

Status: low-risk warning; build succeeds. Can be handled after pilot stabilization.

3. Duplicate/stale frontend files remain.

Examples: `README copy.md`, `package-lock copy.json`, mock `ReportsTable.tsx`.

Status: not removed during stabilization to avoid unnecessary churn.

## Low Issues

1. `.env` has duplicate `DATABASE_URL` and both `JWT_SECRET` and `JWT_SECRET_KEY`.

Status: runtime uses `JWT_SECRET_KEY`; duplicate config should be cleaned before production packaging.

2. Some comments contain mojibake from earlier collaborative edits.

Status: non-runtime issue.

## Repairs Applied

- Stabilized backend launch from both workspace root and backend root.
- Normalized backend environment and storage paths.
- Fixed API trailing-slash integration bug.
- Fixed upload XHR endpoint path.
- Reworked reporting UUID model/schema/service/migration.
- Repaired local SQLite `reports` table.
- Fixed report frontend contract and derived UI metrics from `json_payload`.
- Made Arabic PDF font lookup case-tolerant.
- Declared PDF dependencies in `pyproject.toml`.

## Verification

Commands completed successfully:

- Backend import from workspace root.
- Backend import from backend root.
- Alembic single-head check.
- Python compile checks for touched backend modules.
- Next.js production build.
- Root-launched Uvicorn end-to-end pilot smoke test.

Known verification warning:

- `next build` passes, but warns that `middleware.ts` is deprecated in favor of proxy.

