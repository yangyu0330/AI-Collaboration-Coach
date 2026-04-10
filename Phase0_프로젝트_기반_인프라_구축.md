# Phase 0: 프로젝트 기반 인프라 구축 — 구체화된 계획서

> **상위 문서**: [implementation_plan.md](file:///c:/Users/andyw/Desktop/Like_a_Lion_myproject/implementation_plan.md)
> **기술 스택**: [기술_스택_추천서.md](file:///c:/Users/andyw/Desktop/Like_a_Lion_myproject/%EA%B8%B0%EC%88%A0_%EC%8A%A4%ED%83%9D_%EC%B6%94%EC%B2%9C%EC%84%9C.md)
> **작성일**: 2026-04-09
> **예상 난이도**: ⭐⭐
> **예상 소요 시간**: 2~3시간

---

## 🎯 이 Phase의 목표

Phase 0이 끝나면 다음이 완성되어야 합니다:

1. ✅ 전체 디렉토리 구조가 생성됨
2. ✅ FastAPI 서버가 `GET /health`에 응답함
3. ✅ Supabase PostgreSQL에 연결이 확인됨
4. ✅ Redis에 연결이 확인됨
5. ✅ Celery Worker가 기동됨
6. ✅ Docker Compose로 로컬 개발 환경이 한 번에 올라감
7. ✅ `.env.example`과 환경 변수 관리가 설정됨

---

## 📋 작업 목록 (총 7단계)

### Step 0-1. 프로젝트 루트 디렉토리 구조 생성

프로젝트 루트: `c:\Users\andyw\Desktop\Like_a_Lion_myproject\`

```text
Like_a_Lion_myproject/
│
├── apps/
│   ├── api/                          # FastAPI 메인 서버
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 앱 엔트리포인트
│   │   ├── config.py                 # Pydantic Settings 기반 환경설정
│   │   ├── dependencies.py           # FastAPI Dependency Injection
│   │   └── routers/                  # API 라우터 모듈 (Phase 2~부터 추가)
│   │       └── __init__.py
│   │
│   ├── bot/                          # Telegram Bot 로직 (Phase 2에서 구현)
│   │   └── __init__.py
│   │
│   └── worker/                       # Celery 비동기 워커
│       ├── __init__.py
│       ├── celery_app.py             # Celery 인스턴스 설정
│       └── tasks/                    # 태스크 모듈 (Phase 4~부터 추가)
│           └── __init__.py
│
├── packages/
│   ├── core/                         # 공통 도메인 로직 (Phase 2~부터)
│   │   └── __init__.py
│   │
│   ├── llm/                          # LLM 프롬프트, 분석기 (Phase 5에서 구현)
│   │   └── __init__.py
│   │
│   ├── db/                           # DB 모델, 세션, 마이그레이션
│   │   ├── __init__.py
│   │   ├── session.py                # AsyncSession 팩토리
│   │   ├── base.py                   # DeclarativeBase, 공통 Mixin
│   │   └── models/                   # ORM 모델 (Phase 1에서 구현)
│   │       └── __init__.py
│   │
│   └── shared/                       # 공통 타입, 상수, 유틸
│       ├── __init__.py
│       └── enums.py                  # Enum 정의 (Phase 1에서 구현)
│
├── docs/                             # 프로젝트 문서
│   └── (기존 문서들 유지)
│
├── data/
│   ├── samples/                      # 샘플 데이터
│   └── fixtures/                     # 테스트 픽스처
│
├── scripts/                          # 유틸리티 스크립트
│   └── __init__.py
│
├── tests/                            # 테스트
│   ├── __init__.py
│   ├── conftest.py                   # pytest 공통 설정
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── e2e/
│       └── __init__.py
│
├── .env.example                      # 환경 변수 템플릿
├── .gitignore
├── docker-compose.yml                # 로컬 개발용 Docker Compose
├── Dockerfile                        # FastAPI 서버 이미지
├── pyproject.toml                    # Python 프로젝트 설정
└── README.md                         # 프로젝트 소개 및 실행 방법
```

> [!NOTE]
> `apps/web/` (React + Vite 프론트엔드)는 Phase 8에서 생성합니다.
> 지금은 백엔드 인프라에 집중합니다.

---

### Step 0-2. Python 프로젝트 설정 (`pyproject.toml`)

```toml
[project]
name = "ai-collab-coach"
version = "0.1.0"
description = "AI 협업 코치 - 텔레그램 기반 준실시간 프로젝트 메모리 및 변경 추적 시스템"
requires-python = ">=3.11"
dependencies = [
    # Web Framework
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",

    # Database
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",

    # Task Queue
    "celery>=5.4",
    "redis>=5.0",

    # Telegram Bot (Phase 2에서 사용)
    "python-telegram-bot>=21.0",

    # LLM (Phase 5에서 사용)
    "openai>=1.50",

    # HTTP
    "httpx>=0.27",

    # Config & Validation
    "pydantic>=2.5",
    "pydantic-settings>=2.1",

    # Logging
    "structlog>=24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.5",
    "httpx",  # TestClient용
]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

### Step 0-3. 환경 변수 설정 (`.env.example`)

```env
# ============================================
# AI 협업 코치 - 환경 변수 설정
# ============================================
# 이 파일을 복사하여 .env를 만드세요:
#   cp .env.example .env

# --- Database (Supabase) ---
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres

# --- Redis ---
REDIS_URL=redis://localhost:6379/0

# --- Telegram Bot (Phase 2에서 사용) ---
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
TELEGRAM_SECRET_TOKEN=your-webhook-secret

# --- OpenAI (Phase 5에서 사용) ---
OPENAI_API_KEY=sk-your-openai-api-key

# --- App ---
APP_ENV=development
SECRET_KEY=your-secret-key-change-in-production
DEBUG=true

# --- Session (대화 세션화, Phase 4에서 사용) ---
SESSION_IDLE_THRESHOLD_MINUTES=60

# --- LLM (Phase 5에서 사용) ---
LLM_CONFIDENCE_THRESHOLD=0.7
```

---

### Step 0-4. FastAPI 앱 & 설정

#### `apps/api/config.py` — Pydantic Settings 기반 환경설정

```python
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., description="Supabase PostgreSQL 연결 URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Telegram (Phase 2)
    telegram_bot_token: str = Field(default="")
    webhook_url: str = Field(default="")
    telegram_secret_token: str = Field(default="")

    # OpenAI (Phase 5)
    openai_api_key: str = Field(default="")

    # App
    app_env: str = Field(default="development")
    secret_key: str = Field(default="dev-secret-key")
    debug: bool = Field(default=True)

    # Session (Phase 4)
    session_idle_threshold_minutes: int = Field(default=60)

    # LLM (Phase 5)
    llm_confidence_threshold: float = Field(default=0.7)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# 싱글턴 인스턴스
settings = Settings()
```

#### `apps/api/main.py` — FastAPI 앱 엔트리포인트

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from contextlib import asynccontextmanager

from apps.api.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 로직"""
    logger.info("app_starting", env=settings.app_env)
    yield
    logger.info("app_shutting_down")


app = FastAPI(
    title="AI 협업 코치 API",
    description="텔레그램 기반 준실시간 프로젝트 메모리 및 변경 추적 시스템",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React + Vite 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "env": settings.app_env,
    }


@app.get("/health/db")
async def health_check_db():
    """DB 연결 확인 엔드포인트"""
    from packages.db.session import get_engine
    from sqlalchemy import text

    engine = get_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@app.get("/health/redis")
async def health_check_redis():
    """Redis 연결 확인 엔드포인트"""
    import redis.asyncio as aioredis

    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}
```

#### `apps/api/dependencies.py` — FastAPI DI

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.session import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """DB 세션 의존성 주입"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

### Step 0-5. DB 세션 설정 (Supabase 연결)

#### `packages/db/session.py`

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)
from apps.api.config import settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """AsyncEngine 싱글턴"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,       # SQL 로그 출력 (개발 시)
            pool_size=5,               # 커넥션 풀 크기
            max_overflow=10,           # 초과 허용 커넥션
            pool_pre_ping=True,        # 연결 유효성 검사
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """AsyncSession 팩토리"""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


# 팩토리 인스턴스
async_session_factory = get_session_factory()
```

#### `packages/db/base.py` — 공통 Base & Mixin (Phase 1에서 확장)

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """모든 모델의 베이스 클래스"""
    pass


class UUIDMixin:
    """UUID PK 믹스인"""
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """생성/수정 시각 믹스인"""
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        default=None,
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

---

### Step 0-6. Celery Worker 설정

#### `apps/worker/celery_app.py`

```python
from celery import Celery
from apps.api.config import settings

celery_app = Celery(
    "ai_collab_coach",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    # 직렬화
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 시간대
    timezone="Asia/Seoul",
    enable_utc=True,

    # 재시도
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # 태스크 자동 검색 (Phase 4~에서 추가)
    task_routes={
        "apps.worker.tasks.session_tasks.*": {"queue": "session"},
        "apps.worker.tasks.analysis_tasks.*": {"queue": "analysis"},
        "apps.worker.tasks.notification_tasks.*": {"queue": "notification"},
    },
)

# 태스크 모듈 자동 검색
celery_app.autodiscover_tasks([
    "apps.worker.tasks",
])
```

#### `apps/worker/tasks/__init__.py` — 샘플 태스크 (연결 확인용)

```python
from apps.worker.celery_app import celery_app


@celery_app.task(name="health_check_task")
def health_check_task():
    """워커 연결 확인용 테스트 태스크"""
    return {"status": "ok", "worker": "celery"}
```

---

### Step 0-7. Docker & 기타 설정 파일

#### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# 소스 코드 복사
COPY . .

# uvicorn 서버 실행
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### `docker-compose.yml` (로컬 개발용)

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - redis
    command: uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build: .
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A apps.worker.celery_app worker --loglevel=info --concurrency=2

  beat:
    build: .
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A apps.worker.celery_app beat --loglevel=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

> [!NOTE]
> **PostgreSQL 컨테이너가 없습니다** — Supabase를 사용하므로
> `.env`의 `DATABASE_URL`로 외부 연결합니다.

#### `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# 환경
.env
.venv/
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml

# 테스트
.coverage
htmlcov/
.pytest_cache/

# Celery
celerybeat-schedule
celerybeat.pid
```

#### `README.md`

```markdown
# 🤖 AI 협업 코치

텔레그램 기반 준실시간 프로젝트 메모리 및 변경 추적 시스템

## 빠른 시작

### 1. 환경 변수 설정
\```bash
cp .env.example .env
# .env 파일을 열어 Supabase URL, API 키 등을 입력하세요
\```

### 2. Docker로 실행
\```bash
docker-compose up --build
\```

### 3. 서버 확인
- API 서버: http://localhost:8000
- Health Check: http://localhost:8000/health
- API 문서: http://localhost:8000/docs
- DB 연결 확인: http://localhost:8000/health/db
- Redis 연결 확인: http://localhost:8000/health/redis

### 로컬 개발 (Docker 없이)

\```bash
# 가상환경 생성
python -m venv .venv
.venv\Scripts\activate  # Windows

# 의존성 설치
pip install -e ".[dev]"

# Redis 실행 (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# API 서버 실행
uvicorn apps.api.main:app --reload --port 8000

# Celery Worker 실행 (별도 터미널)
celery -A apps.worker.celery_app worker --loglevel=info
\```

## 기술 스택

| 영역 | 기술 |
|------|------|
| 백엔드 | FastAPI (Python 3.11+) |
| DB | Supabase (PostgreSQL) |
| 워커 | Celery + Redis |
| 프론트 | React + Vite (Phase 8) |
| LLM | OpenAI GPT-4.1 |
| 봇 | python-telegram-bot |
| 배포 | Railway |

## 프로젝트 구조

\```
apps/api/       → FastAPI 서버
apps/bot/       → Telegram Bot
apps/worker/    → Celery Worker
packages/db/    → DB 모델/세션
packages/llm/   → LLM 프롬프트
packages/core/  → 도메인 로직
packages/shared/ → 공통 유틸
\```
\```
```

#### `tests/conftest.py`

```python
"""pytest 공통 설정"""
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
```

---

## ✅ 검증 체크리스트

Phase 0 완료 시 아래를 **순서대로** 검증합니다:

### 1단계: 기본 구조 확인
```bash
# 프로젝트 루트에서
python -c "from apps.api.main import app; print('✅ FastAPI import 성공')"
python -c "from apps.worker.celery_app import celery_app; print('✅ Celery import 성공')"
python -c "from packages.db.session import get_engine; print('✅ DB session import 성공')"
```

### 2단계: 로컬 서버 기동
```bash
uvicorn apps.api.main:app --reload --port 8000
```
- `GET http://localhost:8000/health` → `{"status": "ok", "version": "0.1.0", "env": "development"}`
- `GET http://localhost:8000/docs` → Swagger UI 정상 표시

### 3단계: DB 연결 확인
```bash
# .env에 Supabase DATABASE_URL 설정 후
GET http://localhost:8000/health/db
```
→ `{"status": "ok", "database": "connected"}`

### 4단계: Redis 연결 확인
```bash
docker run -d -p 6379:6379 redis:7-alpine
GET http://localhost:8000/health/redis
```
→ `{"status": "ok", "redis": "connected"}`

### 5단계: Docker Compose 전체 기동
```bash
docker-compose up --build
```
- api, worker, beat, redis 4개 서비스 모두 정상 기동
- `GET http://localhost:8000/health` → 200 OK

---

## 📄 이 Phase의 최종 산출물 목록

| # | 파일 | 설명 |
|:---:|------|------|
| 1 | `pyproject.toml` | Python 프로젝트 설정 + 의존성 |
| 2 | `.env.example` | 환경 변수 템플릿 |
| 3 | `.gitignore` | Git 제외 파일 목록 |
| 4 | `Dockerfile` | FastAPI 서버 이미지 |
| 5 | `docker-compose.yml` | 로컬 개발용 Compose |
| 6 | `README.md` | 프로젝트 소개 + 실행 방법 |
| 7 | `apps/api/main.py` | FastAPI 앱 (health check 포함) |
| 8 | `apps/api/config.py` | Pydantic Settings 환경설정 |
| 9 | `apps/api/dependencies.py` | FastAPI DI |
| 10 | `apps/api/routers/__init__.py` | 라우터 패키지 |
| 11 | `apps/bot/__init__.py` | 봇 패키지 (빈 파일) |
| 12 | `apps/worker/celery_app.py` | Celery 설정 |
| 13 | `apps/worker/tasks/__init__.py` | 테스트 태스크 |
| 14 | `packages/db/session.py` | AsyncSession 팩토리 |
| 15 | `packages/db/base.py` | Base + Mixin |
| 16 | `packages/db/models/__init__.py` | 모델 패키지 (빈 파일) |
| 17 | `packages/shared/enums.py` | Enum 패키지 (빈 파일) |
| 18 | `tests/conftest.py` | pytest 공통 설정 |
| 19-27 | 각 디렉토리의 `__init__.py` | 패키지 초기화 파일들 |

**총 27개 파일** 생성

---

## ⏭️ 다음 Phase 연결

Phase 0 완료 후 **Phase 1 (DB 스키마 & ORM 모델)** 로 진행합니다:
- `packages/db/models/` 디렉토리에 15개 테이블의 ORM 모델 생성
- Alembic 마이그레이션 설정 및 초기 마이그레이션 실행
- Supabase에 테이블 자동 생성
