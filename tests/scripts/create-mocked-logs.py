#!/usr/bin/env python3
from datetime import datetime as _dt
from locale import LC_TIME, setlocale
from logging import Formatter, getLogger
from logging.handlers import RotatingFileHandler
from os import makedirs
from prettyconf import config
from random import random, sample
from re import match
from time import sleep

MOCKED_REQUESTERS = {
    "nando@company.co": "45.33.32.156",
    "renan@company": "198.51.100.14",
    "bono@petshop.com": "203.0.113.73",
    "fred": "91.198.174.192",
    "calasans@home.homenet": "10.1.1.17",
}

MOCKED_REQUESTS = ("/", "/index", "/users", "/user?123", "/product?654", "/purchase")

LOG_TYPE = config("LOG_TYPE", default="http").upper()
LOGS_DIR = config("{}_LOGS_DIR".format(LOG_TYPE), default="/tmp/tests/http")
LOGS_LANG = config("{}_LOGS_LANG".format(LOG_TYPE), default="en_US")
LOGS_TIMEZONE = config("{}_LOGS_TIMEZONE".format(LOG_TYPE), default="+00:00")

LOG_PATTERN = r'{ip} - {user} [{timestamp}] "{method} {uri} HTTP/9.9" {code} 999'
TIMESTAMP_PATTERN = r"%d/%b/%Y:%H:%M:%S {timezone}"
LOGS_PATH = "{}/http-access.log".format(LOGS_DIR)

if LOG_TYPE == "APP":
    LOG_PATTERN = r'{timestamp} [{level}] {page}: {message} {param}'
    TIMESTAMP_PATTERN = r"%F %T"
    LOGS_PATH = "{}/app.log".format(LOGS_DIR)

LOG_LINES = config("LOG_LINES", default="99", cast=int)

print("# To limit the number of logs, run `make test-create-http-logs LOG_LINES=100` or edit env.toml")
print("# Other vars can be set in the [dev] session of the env.toml file before running from `make`")

setlocale(LC_TIME, "{}.UTF-8".format(LOGS_LANG))
print("Locale set to {}.UTF-8. Start creation of mocked logs for {}:".format(LOGS_LANG, LOG_TYPE))

try:
    created_logs = -1
    users = list(MOCKED_REQUESTERS) * 3 + ["-"]

    makedirs(LOGS_DIR, exist_ok=True)
    handler = RotatingFileHandler(LOGS_PATH, maxBytes=100 * 1024, backupCount=3)
    formatter = Formatter('%(message)s')
    handler.setFormatter(formatter)
    log = getLogger()
    log.setLevel("DEBUG")
    log.addHandler(handler)

    for created_logs in range(LOG_LINES):
        log_vars = {"timestamp": _dt.now().strftime(TIMESTAMP_PATTERN.format(timezone=LOGS_TIMEZONE))}

        if LOG_TYPE == "APP":
            level = sample(("DEBUG", "DEBUG", "INFO", "INFO", "WARNING", "ERROR", "CRITICAL"), k=1)[0]
            uri = match(r"^/([^?]*)\??(.*)$", sample(MOCKED_REQUESTS, k=1)[0])
            msg = "Process failed" if level in ("ERROR", "CRITICAL") else "Respond request"

            log_vars["level"] = level
            log_vars["page"] = uri.group(1) or "index"
            log_vars["message"] = "{} for {}".format(msg, uri.group(1) or "/")
            log_vars["param"] = uri.group(2)

        else:
            log_vars["user"] = sample(users, k=1)[0]
            log_vars["ip"] = MOCKED_REQUESTERS.get(log_vars["user"], "199.199.199.199")
            log_vars["method"] = sample(("GET", "GET", "GET", "POST", "POST", "PUT"), k=1)[0]
            log_vars["code"] = sample((200, 200, 200, 201, 201, 302, 401, 503), k=1)[0]
            log_vars["uri"] = sample(MOCKED_REQUESTS, k=1)[0]

        log.debug(LOG_PATTERN.format(**log_vars))

        if created_logs > 0:
            print("\rCreated {}/{} lines of log ".format(created_logs + 1, LOG_LINES), end="")

            if created_logs % 3 == 0:
                sleep(random())

except KeyboardInterrupt:
    print("\rCreation aborted by user request.")

finally:
    print("\rCreated {} lines of log in {}".format(created_logs + 1, LOGS_DIR))
