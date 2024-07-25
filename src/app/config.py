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


APP_NAME: str = config('APP_NAME', default='App Name')
# PROJECT_NAME: str = config('PROJECT_NAME', default='project-name')  # Syntaxes: "lowercasedword", "lowercased-words"
# APP_VERSION: str = config('APP_VERSION', default='1.0.0')
# PROJECT_DESCRIPTION: str = config('PROJECT_DESCRIPTION', default='{} v{}'.format(APP_NAME, APP_VERSION))


HTTP_TOPIC_NAME: str = config('HTTP_TOPIC_NAME', default='requests')
APP_TOPIC_NAME: str = config('APP_TOPIC_NAME', default='responses')


# APP_BIND_HOST: str = config('APP_BIND_HOST', default='127.0.0.1')
# APP_BIND_PORT: int = config('APP_BIND_PORT', default=8080, cast=int)


KAFKA_SERVERS = []  # to be dynamically set and published as tuple
for item in config('KAFKA_SERVERS', default='').split(','):
    if item and item not in KAFKA_SERVERS:
        KAFKA_SERVERS.append(item)
KAFKA_SERVERS = tuple(KAFKA_SERVERS)
