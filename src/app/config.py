#! /usr/bin/env python
"""Main configuration file for this project

*** UPDATE env.toml AND RUN `make` or `make self-test` TO SET .env ***

All env vars values and fallback or default values to be used in the Application.
This module must only be updated in order to:
- Add/remove vars imported from .env
- Update fallback values

Using the Makefile for every command will keep .env updated:
- Values in .env file are not persistent: update env.toml instead
- The .env file may be deployed to Production after build

About prettyconf, dependency responsible for fetching env vars:
- From env vars, Application vars are set
- Precedence: command line var > .env > fallback value (if set)
"""
from prettyconf import config


LOG_LEVEL: str = config('LOG_LEVEL', default='INFO')

# PROJECT_NAME: str = config('PROJECT_NAME', default='project-name')  # Syntaxes: "lowercasedword", "lowercased-words"
# APP_NAME: str = config('APP_NAME', default='App Name')
# APP_VERSION: str = config('APP_VERSION', default='1.0.0')
# PROJECT_DESCRIPTION: str = config('PROJECT_DESCRIPTION', default='{} v{}'.format(APP_NAME, APP_VERSION))

# APP_DIR: str = config('APP_DIR', default='app')
# DATA_DIR: str = config('DATA_DIR', default='data')
# LOGS_DIR: str = config('LOGS_DIR', default='/tmp/{}'.format(PROJECT_NAME))

# LOG_ROTATION_MAX_MB: float = config('LOG_ROTATION_MAX_MB', default=3, cast=float)  # type: ignore
# LOG_MAX_ROTATED_FILES: int = config('LOG_MAX_ROTATED_FILES', default=9, cast=int)

# DB_CONN_STRING: str = config('DB_CONN_STRING', default=None)
# API_BIND_HOST: str = config('API_BIND_HOST', default='127.0.0.1')
# API_BIND_PORT: int = config('API_BIND_PORT', default=5000, cast=int)
# APP_BIND_HOST: str = config('APP_BIND_HOST', default='127.0.0.1')
# APP_BIND_PORT: int = config('APP_BIND_PORT', default=8080, cast=int)


KAFKA_SERVERS = []  # to be dynamically set and published as tuple
for item in config('KAFKA_SERVERS', default='').split(','):
    if item and item not in KAFKA_SERVERS:
        KAFKA_SERVERS.append(item)
KAFKA_SERVERS = tuple(KAFKA_SERVERS)
