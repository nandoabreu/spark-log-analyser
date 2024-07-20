#!/usr/bin/env python3
from datetime import datetime as _dt
from locale import LC_TIME, setlocale
from logging import Formatter, getLogger
from logging.handlers import RotatingFileHandler
from os import makedirs
from prettyconf import config
from random import random, sample
from time import sleep

# 10.4.0.1 - - [18/Apr/2024:14:38:42 +0100] "GET / HTTP/1.1" 200 43229
# 10.4.0.1 - remoteuser [18/Apr/2024:14:37:15 +0100] "POST /dosignin HTTP/1.1" 302 185
# 10.4.0.1 - remoteuser [18/Apr/2024:14:39:02 +0100] "GET /status/operational.json?agent=banner HTTP/1.1" 200 6191
HTTP_LOG_PATTERN = r'{ip} - {user} [{timestamp}] "{method} {uri} HTTP/9.9" {code} 999'

MOCKED_REQUESTERS = {
    "nando@company.co": "45.33.32.156",
    "renan@company": "198.51.100.14",
    "bono@petshop.com": "203.0.113.73",
    "fred": "91.198.174.192",
    "calasans@home.homenet": "10.1.1.17",
}

MOCKED_REQUESTS = ("/", "/index", "/user", "/product?123")

HTTP_LOGS_DIR = config("HTTP_LOGS_DIR", default="/tmp/tests/http")
HTTP_LOGS_LANG = config("HTTP_LOGS_LANG", default="en_US")
HTTP_LOGS_TIMEZONE = config("HTTP_LOGS_TIMEZONE", default="+00:00")

setlocale(LC_TIME, "{}.UTF-8".format(HTTP_LOGS_LANG))
print("Locale set to {}".format(HTTP_LOGS_LANG))

HTTP_LOG_LINES = config("HTTP_LOG_LINES", default="99", cast=int)
LOGS_PATH = "{}/http-access.log".format(HTTP_LOGS_DIR)

try:
    created_logs = -1
    users = list(MOCKED_REQUESTERS) * 3 + ["-"]

    makedirs(HTTP_LOGS_DIR, exist_ok=True)
    handler = RotatingFileHandler(LOGS_PATH, maxBytes=100 * 1024, backupCount=3)
    formatter = Formatter('%(message)s')
    handler.setFormatter(formatter)
    log = getLogger()
    log.setLevel("DEBUG")
    log.addHandler(handler)
    print("Start creating {} lines of log".format(HTTP_LOG_LINES))
    print("+ to limit the number of logs, run `make test-create-http-logs HTTP_LOG_LINES=100` or edit env.toml")
    print("+ other vars cane be set in the [dev] session of the env.toml file: ")

    for created_logs in range(HTTP_LOG_LINES):
        user = sample(users, k=1)[0]
        ip = MOCKED_REQUESTERS.get(user, "199.199.199.199")
        timestamp = (_dt.now()).strftime("%d/%b/%Y:%H:%M:%S {}".format(HTTP_LOGS_TIMEZONE))
        method = sample(("GET", "GET", "GET", "POST", "POST", "PUT"), k=1)[0]
        code = sample((200, 200, 200, 201, 201, 302, 401, 503), k=1)[0]
        uri = sample(MOCKED_REQUESTS, k=1)[0]

        log.debug(HTTP_LOG_PATTERN.format(ip=ip, user=user, timestamp=timestamp, method=method, uri=uri, code=code))

        if (created_logs + 1) % min(int(HTTP_LOG_LINES * .1), 100) == 0:
            print("Created {} lines of log".format(created_logs + 1))

        if (created_logs + 1) % 3:
            sleep(random())

except KeyboardInterrupt:
    pass

finally:
    print("Created {} lines of log in {}".format(created_logs + 1, HTTP_LOGS_DIR))
