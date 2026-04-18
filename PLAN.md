# AROP MVP — Implementation Plan

## Project Overview

**AROP (AI Reliability & Observability Platform)** — a universal proxy + dashboard that logs, replays, guardrails, and analyzes every AI API request/response.

- **Proxy Gateway**: Python FastAPI — intercepts AI calls, applies guardrails, logs traces
- **Dashboard**: Next.js 14 — trace explorer, replay, guardrails UI, cost analytics
- **Database**: PostgreSQL (Docker locally, Supabase/Railway in prod)

---

## Complete File Structure

```
E:/arop/
├── docker-compose.yml
├── README.md
├── .gitignore
│
├── proxy/                          # FastAPI backend (proxy + API)
│   ├── main.py                     # App entry point, mounts all routers
│   ├── config.py                   # Settings via pydantic-settings (.env)
│   ├── database.py                 # asyncpg pool + SQLAlchemy async engine
│   ├── models.py                   # SQLAlchemy ORM models (Trace, Guardrail, ApiKey)
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── dependencies.py             # API key auth dependency
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── proxy.py                # POST /v1/chat/completions
│   │   ├── traces.py               # GET/POST /v1/traces, GET /v1/traces/{id}
│   │   ├── replay.py               # POST /v1/replay
│   │   ├── guardrails.py           # GET/POST /v1/guardrails, PATCH toggle
│   │   ├── analytics.py            # GET /v1/analytics/cost
│   │   └── ingest.py               # POST /v1/ingest/trace (internal)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── guardrail_engine.py     # Pre/post guardrail logic (regex block + PII redact)
│   │   ├── hasher.py               # SHA-256 prompt+response hashing
│   │   ├── llm_client.py           # httpx async forwarding to OpenAI/Anthropic
│   │   ├── cost_calculator.py      # Token -> USD cost lookup table
│   │   └── trace_logger.py         # Async background task: write trace to DB
│   │
│   ├── migrations/
│   │   ├── 001_initial_schema.sql  # CREATE TABLE traces, guardrails, api_keys
│   │   └── run_migrations.py       # Script to apply .sql files via asyncpg
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # pytest fixtures (test DB, test client, mock LLM)
│       ├── test_proxy.py           # Proxy forwarding, guardrail blocking
│       ├── test_guardrail_engine.py
│       ├── test_traces.py          # Trace CRUD API tests
│       ├── test_replay.py
│       └── test_analytics.py
│
└── dashboard/                      # Next.js 14 App Router
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── tsconfig.json
    ├── .env.local.example
    │
    ├── app/
    │   ├── layout.tsx              # Root layout: sidebar nav + topbar
    │   ├── page.tsx                # Redirect to /traces
    │   ├── globals.css
    │   │
    │   ├── traces/
    │   │   ├── page.tsx            # Trace Explorer list page
    │   │   └── [id]/
    │   │       └── page.tsx        # Trace Detail page
    │   │
    │   ├── replay/
    │   │   └── page.tsx            # Replay page (side-by-side)
    │   │
    │   ├── guardrails/
    │   │   └── page.tsx            # Guardrails list + add rule
    │   │
    │   ├── analytics/
    │   │   └── page.tsx            # Cost Analytics page
    │   │
    │   └── settings/
    │       └── page.tsx            # API key management
    │
    ├── components/
    │   ├── ui/                     # ShadCN generated components
    │   ├── layout/
    │   │   ├── Sidebar.tsx
    │   │   └── Topbar.tsx
    │   ├── traces/
    │   │   ├── TraceTable.tsx
    │   │   ├── TraceFilters.tsx
    │   │   └── TraceDetail.tsx
    │   ├── replay/
    │   │   ├── ReplayPanel.tsx
    │   │   └── DiffView.tsx
    │   ├── guardrails/
    │   │   ├── GuardrailList.tsx
    │   │   └── AddGuardrailForm.tsx
    │   ├── analytics/
    │   │   ├── CostOverTime.tsx
    │   │   ├── CostByModel.tsx
    │   │   └── CostByFeature.tsx
    │   └── settings/
    │       └── ApiKeyManager.tsx
    │
    └── lib/
        ├── api.ts                  # Typed fetch wrapper for backend
        ├── types.ts                # Shared TypeScript types
        └── utils.ts                # cn() helper, formatters
```

---

## Database Schema

### Table: traces
```sql
id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
trace_id          TEXT UNIQUE NOT NULL
user_id           TEXT
model             TEXT NOT NULL
provider          TEXT NOT NULL
request_body      JSONB NOT NULL
response_body     JSONB
prompt_hash       TEXT
response_hash     TEXT
latency_ms        INTEGER
prompt_tokens     INTEGER
completion_tokens INTEGER
total_tokens      INTEGER
cost_usd          NUMERIC(10,6)
status            TEXT NOT NULL    -- success | blocked | error
guardrail_hits    JSONB
parent_trace_id   TEXT             -- for replay traces
created_at        TIMESTAMPTZ DEFAULT NOW()
```

### Table: guardrails
```sql
id         UUID PRIMARY KEY DEFAULT gen_random_uuid()
name       TEXT NOT NULL
type       TEXT NOT NULL    -- pre_request | post_response
pattern    TEXT NOT NULL    -- regex string
action     TEXT NOT NULL DEFAULT 'block'   -- block | redact
enabled    BOOLEAN DEFAULT TRUE
created_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: api_keys
```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
name         TEXT NOT NULL
key_hash     TEXT UNIQUE NOT NULL   -- SHA-256 of raw key
created_at   TIMESTAMPTZ DEFAULT NOW()
last_used_at TIMESTAMPTZ
```

---

## Build Sequence (Phases)

| Phase | What to build | Milestone |
|-------|--------------|-----------|
| 1 | docker-compose.yml, .gitignore, proxy/.env.example, proxy/requirements.txt | Can start Postgres |
| 2 | config.py, database.py, models.py, schemas.py | DB layer ready |
| 3 | migrations/001_initial_schema.sql, run_migrations.py | Tables created |
| 4 | services/ (guardrail_engine, hasher, cost_calculator, llm_client) | Core logic |
| 5 | dependencies.py, trace_logger.py | Auth + logging |
| 6 | routers/proxy.py, main.py | Proxy works end-to-end |
| 7 | routers/ (ingest, traces, guardrails, replay, analytics) | Full API |
| 8 | tests/ (conftest + all test files) | Tests passing |
| 9 | dashboard scaffold + lib/ (types, api, utils) | Frontend foundation |
| 10 | dashboard components/ | UI components |
| 11 | dashboard app/ pages | Full UI |
| 12 | Deploy scripts + README | Ship it |

---

## Proxy Gateway Flow (routers/proxy.py)

```
POST /v1/chat/completions
  │
  ├─ 1. Validate X-API-Key header
  ├─ 2. Load guardrail rules (30s cache)
  ├─ 3. check_pre_request(prompt) → if blocked → log trace status=blocked, return 400
  ├─ 4. forward_request(body) → measure latency
  ├─ 5. redact_post_response(response_text)
  ├─ 6. hash prompt + response
  ├─ 7. calculate_cost(model, tokens)
  ├─ 8. BackgroundTask: save_trace(trace_data) → PostgreSQL
  └─ 9. Return response + X-Trace-ID header
```

---

## Key Architectural Decisions

1. **Single FastAPI app** — proxy and backend API are one service, not two
2. **Async-first** — all route handlers use `async def`, asyncpg for DB
3. **Background tasks for logging** — trace write never blocks the response
4. **Guardrail caching** — 30-second in-memory TTL to avoid per-request DB reads
5. **Provider detection by model name** — `claude-*` → Anthropic, else → OpenAI
6. **SHA-256 key hashing** — raw API keys never stored in DB
7. **Client-side dashboard fetching** — simpler than SSR for this internal tool

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Proxy + Backend | Python 3.13, FastAPI, SQLAlchemy async, httpx |
| Dashboard | Next.js 14 (App Router), Tailwind, ShadCN UI, Recharts |
| Database | PostgreSQL (Docker local, Railway prod) |
| Auth | API key (SHA-256 hashed in DB) |
| Deploy | Railway (backend), Vercel (dashboard) |

---

## Local Dev Startup

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Start backend
cd E:/arop/proxy
venv/Scripts/activate
uvicorn main:app --reload --port 8000

# 3. Start dashboard
cd E:/arop/dashboard
npm run dev  # → http://localhost:3000
```

---

## Deploy

**Backend → Railway:**
```bash
cd E:/arop/proxy
railway login && railway init
railway up
```

**Dashboard → Vercel:**
```bash
cd E:/arop/dashboard
vercel --prod
```

---

## MVP Scope (Strictly Excluded)

- A/B prompt testing
- Semantic guardrails (embeddings)
- On-prem deployment
- Teams & RBAC / SSO
- Webhook alerts (add in week 2 if requested)
- Multi-region
