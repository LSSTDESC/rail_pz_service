SHELL := /bin/bash
GIT_BRANCH := $(shell git branch --show-current)
PY_VENV := .venv/
UV_LOCKFILE := uv.lock

#------------------------------------------------------------------------------
# Default help target (thanks ChatGPT)
#------------------------------------------------------------------------------

help:
	@echo "Available targets:"
	@awk -F':' '/^[a-zA-Z0-9\._-]+:/ && !/^[ \t]*\.PHONY/ {print $$1}' $(MAKEFILE_LIST) | sort -u | column


#------------------------------------------------------------------------------
# DX: Use uv to bootstrap project
#------------------------------------------------------------------------------

.PHONY: uv
uv:
	script/bootstrap_uv


$(UV_LOCKFILE):
	uv lock --build-isolation

$(PY_VENV): $(UV_LOCKFILE)
	uv sync --frozen

.PHONY: clean
clean:
	rm -rf $(PY_VENV)
	rm -f test_pz_rail_service.db
	rm -rf ./archive
	find src -type d -name '__pycache__' | xargs rm -rf
	find tests -type d -name '__pycache__' | xargs rm -rf

.PHONY: init
init: $(PY_VENV)
	uv run pre-commit install

.PHONY: update-deps
update-deps: init
	uv lock --upgrade --build-isolation

.PHONY: update
update: update-deps init

.PHONY: build
build: export BUILDKIT_PROGRESS=plain
build:
	docker compose build pz-rail-service-server



#------------------------------------------------------------------------------
# Convenience targets to run pre-commit hooks ("lint") and mypy ("typing")
#------------------------------------------------------------------------------

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: typing
typing:
	mypy src tests


#------------------------------------------------------------------------------
# Targets for develpers to debug against a local Postgres run under docker
# compose. Can be used on local machines and in github CI, but not on USDF dev
# nodes since we can't run docker there.
#------------------------------------------------------------------------------

.PHONY: run-compose
run-compose:
	docker compose up --wait

.PHONY: psql
psql: PGPORT=$(shell docker compose port postgresql 5432 | cut -d: -f2)
psql: export DB__PASSWORD=INSECURE-PASSWORD
psql: run-compose
	psql postgresql://pz-rail-service:${DB__PASSWORD}@localhost:${PGPORT}/pz-rail-service

.PHONY: test
test: PGPORT=$(shell docker compose port postgresql 5432 | cut -d: -f2)
test: export DB__URL=postgresql://pz-rail-service@localhost:${PGPORT}/pz-rail-services-tets
test: export DB__PASSWORD=INSECURE-PASSWORD
test: export DB__TABLE_SCHEMA=pz-rail-services-tets
test: run-compose
	alembic upgrade head
	pytest -vvv --asyncio-mode=auto --cov=rail_pz_service --cov-branch --cov-report=term --cov-report=html ${PYTEST_ARGS}

.PHONY: migrate
migrate: export PGUSER=pz-rail-service
migrate: export PGDATABASE=pz-rail-service
migrate: export PGHOST=localhost
migrate: export DB__PORT=$(shell docker compose port postgresql 5432 | cut -d: -f2)
migrate: export DB__PASSWORD=INSECURE-PASSWORD
migrate: export DB__URL=postgresql://${PGHOST}/${PGDATABASE}
migrate: run-compose
	alembic upgrade head

.PHONY: unmigrate
unmigrate: export PGUSER=pz-rail-service
unmigrate: export PGDATABASE=pz-rail-service
unmigrate: export PGHOST=localhost
unmigrate: export DB__PORT=$(shell docker compose port postgresql 5432 | cut -d: -f2)
unmigrate: export DB__PASSWORD=INSECURE-PASSWORD
unmigrate: export DB__URL=postgresql://${PGHOST}/${PGDATABASE}
unmigrate: run-compose
	alembic downgrade base


#------------------------------------------------------------------------------
# Targets for developers to debug running against local sqlite.  Can be used on
# local machines or USDF dev nodes.
#------------------------------------------------------------------------------

.PHONY: test-sqlite
test-sqlite: export DB__URL=sqlite+aiosqlite:////${PWD}/tests/test_pz_rail_service.db
test-sqlite:
	pytest -vvv --asyncio-mode=auto --cov=rail_pz_service --cov-branch --cov-report=term --cov-report=html ${PYTEST_ARGS}

.PHONY: test-github-ci
test-github-ci: export DB__URL=sqlite+aiosqlite:////${PWD}/tests/test_pz_rail_service.db
test-github-ci:
	pytest -vvv --asyncio-mode=auto --cov=rail_pz_service --cov-branch --cov-report=term --cov-report=xml ${PYTEST_ARGS}

.PHONY: run-sqlite
run-sqlite: export DB__URL=sqlite+aiosqlite:////${PWD}/tests/test_pz_rail_service.db
run-sqlite:
	pz-rail-service-server
