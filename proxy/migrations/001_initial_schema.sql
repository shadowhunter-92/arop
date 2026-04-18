-- AROP initial schema
-- Matches models.py exactly. Run once via run_migrations.py.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- provides gen_random_uuid()

-- ── traces ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS traces (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id            TEXT UNIQUE NOT NULL,
    user_id             TEXT,
    feature             TEXT,
    model               TEXT NOT NULL,
    provider            TEXT NOT NULL,
    -- NULL when hash_payloads=True and store_raw=False (privacy-safe default)
    request_body        JSONB,
    response_body       JSONB,
    prompt_hash         TEXT,
    response_hash       TEXT,
    latency_ms          INTEGER,
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    total_tokens        INTEGER,
    cost_usd            NUMERIC(10, 6),
    status              TEXT NOT NULL,          -- success | blocked | error
    guardrail_hits      JSONB,
    parent_trace_id     TEXT,
    -- User-defined quality signal (0.0–1.0). Updated by POST /v1/evaluate.
    custom_score        FLOAT,
    raw_storage_url     TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_traces_created_at  ON traces (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_user_id     ON traces (user_id);
CREATE INDEX IF NOT EXISTS idx_traces_model       ON traces (model);
CREATE INDEX IF NOT EXISTS idx_traces_status      ON traces (status);
CREATE INDEX IF NOT EXISTS idx_traces_feature     ON traces (feature);

-- ── guardrails ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS guardrails (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,              -- pre_request | post_response
    pattern     TEXT NOT NULL,             -- regex string
    action      TEXT NOT NULL DEFAULT 'block',  -- block | redact
    enabled     BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── api_keys ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS api_keys (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name         TEXT NOT NULL,
    key_hash     TEXT UNIQUE NOT NULL,     -- SHA-256 of raw key; raw key never stored
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- ── pricing_table ─────────────────────────────────────────────────────────────
-- Storing pricing in DB (not hardcoded) means costs can be updated without a deploy.
-- This directly mitigates LangSmith's known cost-accuracy problem.
CREATE TABLE IF NOT EXISTS pricing_table (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model                   TEXT UNIQUE NOT NULL,
    provider                TEXT NOT NULL,
    prompt_cost_per_1m      FLOAT NOT NULL,     -- USD per 1 million prompt tokens
    completion_cost_per_1m  FLOAT NOT NULL,     -- USD per 1 million completion tokens
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Seed current pricing (April 2026). Update rows here as providers change rates.
INSERT INTO pricing_table (model, provider, prompt_cost_per_1m, completion_cost_per_1m) VALUES
    ('gpt-4o',                        'openai',    2.50,   10.00),
    ('gpt-4o-mini',                   'openai',    0.15,    0.60),
    ('gpt-4-turbo',                   'openai',   10.00,   30.00),
    ('gpt-3.5-turbo',                 'openai',    0.50,    1.50),
    ('claude-3-5-sonnet-20241022',    'anthropic', 3.00,   15.00),
    ('claude-3-5-haiku-20241022',     'anthropic', 0.80,    4.00),
    ('claude-3-opus-20240229',        'anthropic',15.00,   75.00),
    ('claude-sonnet-4-6',             'anthropic', 3.00,   15.00),
    ('gemini-1.5-pro',                'google',    1.25,    5.00),
    ('gemini-1.5-flash',              'google',    0.075,   0.30),
    ('gemini-2.0-flash',              'google',    0.10,    0.40)
ON CONFLICT (model) DO NOTHING;
