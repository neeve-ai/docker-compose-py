SHELL  := /bin/bash
.DEFAULT_GOAL := help

VENV      := .venv
PRECOMMIT := $(VENV)/bin/pre-commit

.PHONY: help setup install quality

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { \
		printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

setup: $(PRECOMMIT) ## Create .venv with pre-commit
	@echo "✓ All tools ready  [pre-commit]"

$(PRECOMMIT):
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet pre-commit

install: setup ## Install pre-commit hooks and package
	$(PRECOMMIT) install
	$(PRECOMMIT) install --hook-type prepare-commit-msg
	$(VENV)/bin/pip install setuptools wheel setuptools-download pytest
	$(VENV)/bin/pip install . --no-build-isolation

quality: install ## Run tests and build wheel
	$(VENV)/bin/docker-compose version
	$(VENV)/bin/docker-compose --help
	$(VENV)/bin/pytest tests/
	$(VENV)/bin/pip wheel --no-deps --no-build-isolation --wheel-dir dist .
