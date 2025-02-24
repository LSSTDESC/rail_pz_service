SHELL := /bin/bash
GIT_BRANCH := $(shell git branch --show-current)
PY_VENV := ..venv/
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
