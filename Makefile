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


#------------------------------------------------------------------------------
# Convenience targets to run pre-commit hooks ("lint") and mypy ("typing")
#------------------------------------------------------------------------------

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: typing
typing:
	mypy --config-file mypy.ini -p rail_pz_service.common -p rail_pz_service.client -p rail_pz_service.db -p rail_pz_service.server
