# AROP — AI Reliability & Observability Platform

Drop-in proxy that logs, guardrails, replays, and analyzes every AI API call — across any provider, in any stack.

---

## What it does

| Feature | Description |
|---------|-------------|
| **Trace logging** | Every request/response logged with latency, cost, tokens, status |
| **Guardrails** | Regex rules that block or redact content pre-request and post-response |
| **Replay** | Re-run any past trace with a different model or prompt override |
| **Cost analytics** | Daily cost, by-model, and by-feature breakdowns with live pricing |
| **Quality scores** | Post 0–1 evaluation scores per trace for human-in-the-loop feedback |
| **Privacy mode** | Store only SHA-256 hashes — no plaintext ever touches the database |
| **On-prem** | Full Docker Compose stack — air-gap deployable, data never leaves your network |

---

## Quick Start (Local)

**Prerequisites:** Docker Desktop · Python 3.11+ · Node.js 18+

```bash
# 1. Start PostgreSQL
cd E:/arop
docker compose up -d

# 2. Start the proxy
cd proxy
cp .env.example .env        # fill in your API keys
python -m venv venv
venv/Scripts/activate       # Windows  (source venv/bin/activate on Mac/Linux)
pip install -r requirements.txt
python migrations/run_migrations.py
uvicorn main:app --reload --port 8000

# 3. Start the dashboard
cd ../dashboard
cp .env.local.example .env.local
npm install
npm run dev                 # → http://localhost:3000
```

---

## Integrating with your app

One-line change — swap your `base_url`:

```python
import openai

client = openai.OpenAI(
    api_key="your-openai-key",           # your provider key — AROP forwards it
    base_url="http://localhost:8000/v1",  # ← the only change
    default_headers={
        "X-API-Key": "changeme",         # your AROP_MASTER_KEY
        "X-User-ID": "user_123",         # optional — enables per-user analytics
        "X-Feature": "chatbot",          # optional — enables per-feature cost breakdown
    },
)

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
# Response headers: X-Trace-ID, X-Latency-Ms, X-Cost-USD, X-Hallucination-Score
```

Works identically with Anthropic (`claude-*`) and Google (`gemini-*`) models — AROP auto-detects the provider from the model name and translates the request format.

---

## Supported Providers

| Provider | Model prefix | Notes |
|----------|-------------|-------|
| OpenAI | `gpt-*` | Full support |
| Anthropic | `claude-*` | Auto-translated from OpenAI format |
| Google | `gemini-*` | Via OpenAI-compatible passthrough |
| Any OpenAI-compatible | any | Set `X-Provider-Base-URL` header |

---

## API Reference

### Proxy

```
POST /v1/chat/completions
Headers: X-API-Key (required), X-User-ID (optional), X-Feature (optional)
```

### Traces

```
GET  /v1/traces                     List traces
     ?model=gpt-4o&status=blocked   Filter by model, status, user_id, feature, from, to
     &limit=50&offset=0             Pagination

GET  /v1/traces/{trace_id}          Full trace with request/response bodies

POST /v1/replay                     Re-run a trace
     { trace_id, model_override?,   
       prompt_override? }

POST /v1/evaluate                   Post a quality score
     { trace_id, score: 0.0–1.0 }
```

### Guardrails

```
GET    /v1/guardrails                List all rules
POST   /v1/guardrails                Create a rule { name, type, pattern, action }
PATCH  /v1/guardrails/{id}/toggle    Enable/disable { enabled: bool }
DELETE /v1/guardrails/{id}           Delete a rule
```

### Analytics

```
GET /v1/analytics/cost?from=2024-01-01&to=2024-01-31
→ { over_time: [...], by_model: [...], by_feature: [...], total_cost_usd, total_calls }
```

### Settings

```
GET    /v1/settings/api-keys          List API keys
POST   /v1/settings/api-keys          Create key { name } → returns raw_key once
GET    /v1/settings/pricing           List model pricing
PATCH  /v1/settings/pricing/{model}   Update pricing { prompt_cost_per_1m, completion_cost_per_1m }
```

### System

```
GET /health   → { status: "ok", version: "0.1.0" }
```

---

## Guardrail rules

Rules are Python-compatible regex patterns applied to the full request or response text.

```bash
# Block SSNs in responses
POST /v1/guardrails
{
  "name": "Block SSN",
  "type": "post_response",
  "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
  "action": "block"
}

# Redact credit card numbers
{
  "name": "Redact credit cards",
  "type": "post_response",
  "pattern": "\\b(?:\\d[ -]?){13,16}\\b",
  "action": "redact"
}
```

Built-in PII redaction (always active): email addresses, phone numbers, US SSNs, credit card numbers.

---

## Privacy settings

```bash
# .env (default — maximum privacy)
HASH_PAYLOADS=true    # Only SHA-256 hashes stored. No plaintext in DB.
STORE_RAW=false

# Store raw payloads (opt-in)
HASH_PAYLOADS=true
STORE_RAW=true
RAW_STORAGE_URL=s3://your-bucket/arop-traces/   # optional: off-site storage
```

When `STORE_RAW=false`, the Replay feature requires a `prompt_override` since the original prompt was not stored.

---

## Running tests

```bash
cd proxy
venv/Scripts/activate
pytest tests/ -v
```

74 tests covering: proxy flow, guardrail engine, traces CRUD, replay, analytics, evaluate.

---

## Deploy

### Option A — Railway (backend) + Vercel (dashboard)

```bash
# Backend → Railway
cd proxy
railway login
railway init
railway add postgres        # adds managed PostgreSQL, injects DATABASE_URL
railway up

# Set environment variables in Railway dashboard:
#   AROP_MASTER_KEY    (openssl rand -hex 32)
#   OPENAI_API_KEY
#   ANTHROPIC_API_KEY

# Dashboard → Vercel
cd ../dashboard
vercel --prod

# Set Vercel environment variables:
#   NEXT_PUBLIC_API_URL   = https://your-railway-app.up.railway.app
#   NEXT_PUBLIC_AROP_KEY  = (same as AROP_MASTER_KEY)
```

### Option B — Full stack Docker Compose (on-premises)

```bash
# 1. Copy and configure
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, AROP_MASTER_KEY, OPENAI_API_KEY

# 2. Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Proxy:    http://your-server:8000
# Dashboard: http://your-server:3000
```

```bash
# Useful Makefile shortcuts
make dev-db          # start postgres only
make test            # run proxy tests
make build-prod      # build production Docker images
make up-prod         # start full production stack
make down            # stop production stack
```

### Environment variables reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | `postgresql+psycopg://user:pass@host:5432/db` |
| `AROP_MASTER_KEY` | Yes | `changeme` | Master API key for the proxy |
| `OPENAI_API_KEY` | No | — | Forwarded to OpenAI for `gpt-*` models |
| `ANTHROPIC_API_KEY` | No | — | Forwarded to Anthropic for `claude-*` models |
| `HASH_PAYLOADS` | No | `true` | Store SHA-256 hashes instead of plaintext |
| `STORE_RAW` | No | `false` | Also store raw request/response bodies |
| `RAW_STORAGE_URL` | No | — | S3 path for raw payload storage |

---

## Architecture

```
Your app
  │  POST /v1/chat/completions
  │  X-API-Key: <key>
  ▼
AROP Proxy (FastAPI)
  ├─ 1. Verify API key (SHA-256 hash lookup)
  ├─ 2. Load guardrail rules (30s TTL cache)
  ├─ 3. Pre-request guardrail check → block/pass
  ├─ 4. Forward to provider (OpenAI / Anthropic / custom)
  ├─ 5. Post-response PII redaction
  ├─ 6. Hash prompt + response
  ├─ 7. Calculate cost (live pricing table, 5min TTL cache)
  ├─ 8. Background task: write trace to PostgreSQL
  └─ 9. Return response + X-Trace-ID header
          │
          ▼
AROP Dashboard (Next.js)
  ├─ /traces      — searchable trace explorer
  ├─ /analytics   — cost & usage charts
  ├─ /guardrails  — rule management
  ├─ /replay      — side-by-side diff replay
  └─ /settings    — API keys, model pricing
```

---

## Pricing tiers (planned)

| Plan | Price | Limits |
|------|-------|--------|
| Hobby | Free | 1k traces/month, 7-day retention |
| Pro | $49/month | 30-day retention, guardrails, replay, analytics |
| Enterprise | Custom | On-prem deploy, SOC2 audit, 90-day retention, SSO |
