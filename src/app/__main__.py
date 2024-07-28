#!/usr/bin/env python3
from . import config as cfg
from . import Presentation
from .Logger import log
from .Helper import fetch_host_ip


if __name__ == "__main__":
    local_ip = fetch_host_ip() if cfg.BIND_HOST in ("127.0.0.1", "localhost", "0.0.0.0") else cfg.BIND_HOST
    log.info(f"Start UI at http://{fetch_host_ip()}:{cfg.BIND_PORT}")
    Presentation.run()
