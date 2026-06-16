# GBI-SCIOS Backend

Production-ready FastAPI backend scaffold with PostgreSQL, SQLAlchemy, Alembic, JWT authentication, password hashing, and role support.

## Stack

- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- JWT auth with `python-jose`
- Password hashing with `passlib[bcrypt]`

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Auth APIs

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

## Project APIs

- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{id}`
- `PUT /api/v1/projects/{id}`
- `DELETE /api/v1/projects/{id}`

## Upload APIs

- `POST /api/v1/uploads`
- `GET /api/v1/uploads/project/{project_id}`
- `DELETE /api/v1/uploads/{id}`

Uploaded files are stored locally under `storage/uploads/` in development. The storage service is isolated so an S3 backend can be introduced later without changing the router or database layer.

## BoQ Parsing APIs

- `POST /api/v1/parsing/boq/{uploaded_file_id}`
- `GET /api/v1/parsing/boq/project/{project_id}`

BoQ parsing supports CSV, XLS, and XLSX files through pandas. Required columns are `item_code`, `description`, `quantity`, and `unit_price`; optional columns are `total_price` and `sourcing_type`. Parsing audit logs are written to `storage/parsing_logs/`.

## Compliance APIs

- `POST /api/v1/compliance/mandatory-list/upload`
- `POST /api/v1/compliance/scan/{project_id}`
- `GET /api/v1/compliance/project/{project_id}`

Mandatory list uploads support CSV, XLS, and XLSX files. Compliance scans evaluate imported BoQ items only, match by exact `item_code` first, then fuzzy-match BoQ descriptions against mandatory product names. Scan audit logs are written to `storage/compliance_scan_logs/`.

## Roles

- `Admin`
- `Consultant`
- `Client`
