#! /usr/bin/env python
"""Main configuration file for this project

All env vars values and fallback or default values to be used in the Application.
This module must only be updated in order to:
- Add/remove vars imported from .env
- Update fallback values

Using the Makefile for every command will keep .env updated:
- Values in .env file are not persistent: update env.toml instead
- The .env file may be deployed to Production

*** UPDATE env.toml AND RUN `make` or `make self-test` TO SET .env ***

About prettyconf, dependency responsible for fetching env vars:
- From env vars, Application vars are set
- Precedence: command line var > .env > fallback value (if set)
"""
from prettyconf import config

APP_NAME: str = config("APP_NAME", default="App Name")
# APP_VERSION: str = config("APP_VERSION", default="1.0.0")

# PROJECT_NAME: str = config("PROJECT_NAME", default="project-name")  # Syntaxes: "lowercase", "lower-case"
# PROJECT_DESCRIPTION: str = config("PROJECT_DESCRIPTION", default="{} v{}".format(APP_NAME, APP_VERSION))

LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
LOG_NAME: str = config("LOG_NAME", default=APP_NAME.replace(" ", "-").lower())

HTTP_TOPIC_NAME: str = config("HTTP_TOPIC_NAME", default="requests")
APP_TOPIC_NAME: str = config("APP_TOPIC_NAME", default="responses")

BIND_HOST: str = config("BIND_HOST", default="127.0.0.1")
BIND_PORT: int = config("BIND_PORT", default=8080, cast=int)

KAFKA_SERVERS = []  # to be dynamically set and published as tuple
for item in config("KAFKA_SERVERS", default="").split(","):
    if item and item not in KAFKA_SERVERS:
        KAFKA_SERVERS.append(item)
KAFKA_SERVERS = tuple(KAFKA_SERVERS)
