.PHONY: dev dev-db dev-proxy dev-dashboard test build-prod up-prod down

# ── Local development ─────────────────────────────────────────────────────────

dev-db:
	docker compose up -d

dev-proxy:
	cd proxy && uvicorn main:app --reload --port 8000

dev-dashboard:
	cd dashboard && npm run dev

# Start all three in parallel (requires make 4.x or a shell that supports & )
dev:
	$(MAKE) dev-db
	@echo "Starting proxy and dashboard..."
	@cd proxy && uvicorn main:app --reload --port 8000 & \
	 cd dashboard && npm run dev

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	cd proxy && python -m pytest tests/ -v --tb=short

test-cov:
	cd proxy && python -m pytest tests/ -v --cov=. --cov-report=term-missing

# ── Production (Docker) ───────────────────────────────────────────────────────

build-prod:
	docker compose -f docker-compose.prod.yml build

up-prod:
	docker compose -f docker-compose.prod.yml up -d

down:
	docker compose -f docker-compose.prod.yml down

# ── Migrations ────────────────────────────────────────────────────────────────

migrate:
	cd proxy && python migrations/run_migrations.py
