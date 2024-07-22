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


test-start-kafka:
	@podman run --rm -d --hostname=kafka --name=kafka -p 9092:9092 \
		docker.io/apache/kafka:3.7.0

test-create-mocked-logs:
	@LOG_TYPE=HTTP LOG_LINES=300 poetry run python tests/scripts/create-mocked-logs.py
	@LOG_TYPE=APP LOG_LINES=300 poetry run python tests/scripts/create-mocked-logs.py

test-publish-mocked-logs:
	@PYTHONPATH=src poetry run python tests/scripts/publish-http-logs-to-broker.py

test-created-topics:
	podman exec -it kafka ls -ltr /tmp/kraft-combined-logs | grep -e requests -e responses
