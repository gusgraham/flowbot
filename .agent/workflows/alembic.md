---
description: How to run Alembic migrations for the flowbot_hub project
---

# Running Alembic Migrations

The project uses a virtual environment at `d:\antigravity\flowbot_hub\.venv`.

## Generate a new migration (autogenerate)
// turbo
```powershell
d:\antigravity\flowbot_hub\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "migration_name"
```
Run from: `d:\antigravity\flowbot_hub\backend`

## Apply migrations (upgrade to head)
// turbo
```powershell
d:\antigravity\flowbot_hub\.venv\Scripts\python.exe -m alembic upgrade head
```
Run from: `d:\antigravity\flowbot_hub\backend`

## Downgrade one revision
```powershell
d:\antigravity\flowbot_hub\.venv\Scripts\python.exe -m alembic downgrade -1
```
Run from: `d:\antigravity\flowbot_hub\backend`

## Show migration history
// turbo
```powershell
d:\antigravity\flowbot_hub\.venv\Scripts\python.exe -m alembic history
```
Run from: `d:\antigravity\flowbot_hub\backend`
