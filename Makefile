.PHONY: setup python-sync web-install format format-check lint typecheck test build secrets check dev-api dev-web container-build container-up container-up-prepared container-down container-check clean

setup: python-sync web-install

python-sync:
	uv sync --all-groups --locked

web-install:
	npm ci

format:
	uv run ruff format services/backend
	npm run format

format-check:
	uv run ruff format --check services/backend
	npm run format:check

lint:
	uv run ruff check services/backend
	npm run lint

typecheck:
	uv run mypy services/backend/src
	npm run typecheck

test:
	uv run pytest
	npm run test

build:
	npm run build

secrets:
	git ls-files --cached --others --exclude-standard -z -- ':!.secrets.baseline' | xargs -0 uv run detect-secrets-hook --baseline .secrets.baseline

check: format-check lint typecheck test build secrets

dev-api:
	uv run uvicorn echoatlas.api.app:app --reload

dev-web:
	npm run dev --workspace @echoatlas/workbench

container-build:
	docker compose build

container-up:
	docker compose up --detach --wait

container-up-prepared:
	docker compose -f compose.yaml -f compose.prepared.yaml up --detach --wait

container-down:
	docker compose down --remove-orphans

container-check:
	./scripts/verify-compose.sh

clean:
	rm -rf apps/workbench/dist apps/workbench/coverage .coverage htmlcov
