#!/usr/bin/env make
.PHONY: _

SHELL := $(shell which bash sh | head -1 | cut -d\  -f1)
PYTHON_REQUIRED_VERSION := $(shell cat .python-version 2>/dev/null || grep 'python = ' pyproject.toml | sed "s,[^0-9\.],,g")
PYTHON_EFFECTIVE_VERSION := $(shell python -V | cut -d\  -f2 | cut -d\. -f1-2)
PROJECT_PATH := $(shell realpath .)
poetry_or_python := $(shell which poetry >/dev/null && echo "poetry run python3" || echo "python3")

$(shell eval run=dev "${poetry_or_python}" setup/dotenv-from-toml.py > .env)
include .env


self-test:
	@echo -e """\
	Application: ${APP_NAME} v${APP_VERSION}\n\
	Project: ${PROJECT_NAME} (${PROJECT_DESCRIPTION})\n\
	Virtual env: ${VIRTUAL_ENV}\n\
	Source files: ${PROJECT_PATH}/${SRC_DIR}\n\
	""" | sed "s,: ,:|,;s,^\t,," | column -t -s\|

setup-dev:
	@git init
	@[ $(shell python -c "print(${PYTHON_EFFECTIVE_VERSION} >= ${PYTHON_REQUIRED_VERSION})") == False ] && \
		pyenv local ${PYTHON_REQUIRED_VERSION} || true
	@[ -f .python-version ] && poetry env use $(shell cat .python-version) >/dev/null || true
	@poetry install -v


run:
	@PYTHONPATH=${SRC_DIR} poetry run python -m app

test-start-kafka:
	@podman run --rm -d --network=host --hostname=kafka --name=kafka docker.io/apache/kafka:3.7.0
	@echo "Kafka service should be running on 127.0.0.1, port 9092"

test-start-kafka-ui:
	@podman run --rm -d --network=host -it --hostname=kafka-ui --name=kafka-ui \
		-e DYNAMIC_CONFIG_ENABLED=true \
		docker.io/provectuslabs/kafka-ui
	@echo "Kafka UI should be running on http://127.0.0.1:8080/"

test-create-mocked-logs:
	@LOG_TYPE=HTTP LOG_LINES=300 poetry run python tests/scripts/create-mocked-logs.py
	@LOG_TYPE=APP LOG_LINES=300 poetry run python tests/scripts/create-mocked-logs.py

test-publish-mocked-logs:
	@PYTHONPATH=src poetry run python tests/scripts/publish-logs-to-broker.py

test-created-topics:
	podman exec -it kafka ls -ltr /tmp/kraft-combined-logs | grep -e requests -e responses

test-published-logs:
	@PYTHONPATH=src poetry run python tests/scripts/test-broker-published.py


test-tidy-up:
	@podman stop kafka-ui 2>/dev/null || true
	@podman stop kafka 2>/dev/null || true
