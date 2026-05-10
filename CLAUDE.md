# AROP — Claude Code Agent Config

## Project
AI observability proxy and dashboard. Tracks LLM token usage, costs, latency per API call.
Stage: MVP. Target: $5k MRR. Tech: Python, FastAPI, PostgreSQL, React.

## Parallel Agent Team
| Role | Model | Focus |
|------|-------|-------|
| researcher | mistral:7b | LLM observability market, competitor tools (Helicone, LangSmith) |
| coder | qwen2.5-coder:7b | FastAPI endpoints, proxy logic, dashboard components |
| debugger | qwen2.5-coder:7b | API errors, proxy timeouts, DB query issues |
| pm | llama3.2:3b | Deployment blockers, pricing page, first customer |
| marketer | llama3.2:3b | HN posts, dev community outreach, cold emails |

## CLI-Anything
Plugin at `.claude/plugins/cli-anything/` — use `/cli-anything` for CLI harnesses.

## Revenue Model
SaaS: $29-99/month. Deploy to Railway/Render → post on HN Show HN.

## Priority
Ship a public URL. Everything else is secondary.
