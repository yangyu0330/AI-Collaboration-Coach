# AI Collaboration Coach

Telegram-based project memory and change-tracking system.

## Quick Start

1. Copy env template:

```bash
cp .env.example .env
```

2. Fill `.env` values (`DATABASE_URL`, `REDIS_URL`, API keys).

3. Run all services:

```bash
docker compose up --build
```

4. Check health endpoints:

- `http://localhost:8000/health`
- `http://localhost:8000/health/db`
- `http://localhost:8000/health/redis`
- `http://localhost:8000/docs`

## Local Dev (without Docker)

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn apps.api.main:app --reload --port 8000
```

In a separate terminal for worker:

```bash
celery -A apps.worker.celery_app worker --loglevel=info
```

## Stack

- Backend: FastAPI (Python 3.11+)
- Queue: Celery + Redis
- Database: Supabase PostgreSQL
- LLM: OpenAI API
- Frontend: React + Vite (planned for Phase 8)

