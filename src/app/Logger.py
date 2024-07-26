#!/usr/bin/env python
"""
My Python module
"""
import logging
from sys import stdout

from app.config import LOG_NAME, LOG_LEVEL

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler = logging.StreamHandler(stream=stdout)
handler.setFormatter(formatter)

log = logging.getLogger(LOG_NAME)
log.setLevel(LOG_LEVEL)
log.addHandler(handler)
