#!/usr/bin/env python3
from datetime import datetime as _dt, timedelta
from locale import LC_TIME, setlocale
from prettyconf import config
from random import randint, random, sample

# 10.4.0.1 - - [18/Apr/2024:14:38:42 +0100] "GET / HTTP/1.1" 200 43229
# 10.4.0.1 - remoteuser [18/Apr/2024:14:37:15 +0100] "POST /dosignin HTTP/1.1" 302 185
# 10.4.0.1 - remoteuser [18/Apr/2024:14:39:02 +0100] "GET /status/operational.json?agent=banner HTTP/1.1" 200 6191
HTTP_LOG_LINE_PATTERN = r'{ip} - {user} [{timestamp}] "{method} {uri} HTTP/9.9" {code} 999'

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
print("Locale set: {}".format(HTTP_LOGS_LANG))

HTTP_LOG_LINES = config("HTTP_LOG_LINES", default="99", cast=int)
LOGS_PATH = "{}/http-access.log".format(HTTP_LOGS_DIR)

try:
    users = list(MOCKED_REQUESTERS) * 3 + ["-"]

    print("Start creating {} lines of log".format(LOG_LINES))

    for _ in range(LOG_LINES):
        user = sample(users, k=1)[0]
        ip = MOCKED_REQUESTERS.get(user, "199.199.199.199")
        timestamp = (_dt.now()).strftime("%d/%b/%Y:%H:%M:%S {}".format(HTTP_LOGS_TIMEZONE))
        method = sample(("GET", "GET", "GET", "POST", "POST", "PUT"), k=1)[0]
        code = sample((200, 200, 200, 201, 201, 302, 401, 503), k=1)[0]
        uri = sample(MOCKED_REQUESTS, k=1)[0]

        print(HTTP_LOG_LINE_PATTERN.format(ip=ip, user=user, timestamp=timestamp, method=method, uri=uri, code=code))

except KeyboardInterrupt:
    pass
