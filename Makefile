#!/usr/bin/env make
.PHONY: _

SHELL := $(shell which bash sh | head -1 | cut -d\  -f1)
PYTHON_REQUIRED_VERSION := $(shell cat .python-version 2>/dev/null || grep 'python = ' pyproject.toml | sed "s,[^0-9\.],,g")
PYTHON_EFFECTIVE_VERSION := $(shell python -V | cut -d\  -f2 | cut -d\. -f1-2)
PROJECT_PATH := $(shell realpath .)

$(shell run=dev poetry run python3 setup/dotenv-from-toml.py > .env)
include .env


self-test:
	@echo -e """\
	Application: ${APP_NAME} v${APP_VERSION}\n\
	Project: ${PROJECT_NAME} (${PROJECT_DESCRIPTION})\n\
	Virtual env: $(shell poetry env info -p)\n\
	Source files: ${PROJECT_PATH}/${SRC_DIR}\n\
	""" | sed "s,: ,:|,;s,^\t,," | column -t -s\|

setup-dev:
	@git init
	@[ $(shell python -c "print(${PYTHON_EFFECTIVE_VERSION} >= ${PYTHON_REQUIRED_VERSION})") == False ] && \
		pyenv local ${PYTHON_REQUIRED_VERSION} || true
	@[ -f .python-version ] && poetry env use $(shell cat .python-version) >/dev/null || true
	@poetry install -v

