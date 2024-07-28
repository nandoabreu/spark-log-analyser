#!/usr/bin/env python
"""My Python module

Description
"""
from functools import lru_cache
from pathlib import PosixPath, Path
from subprocess import run as proc_run

try:
    # noinspection PyUnresolvedReferences
    from tomli import load, TOMLDecodeError  # Python < v3.11
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    from tomllib import load, TOMLDecodeError


@lru_cache()
def fetch_host_ip() -> str:
    """Fetch the host's IP address, closest to an available default gateway

    This method fetches the IP Address from the default gateway with  the lowest metric.
    The return defaults to localhost, as 127.0.0.1.
    The method is cached.

    Returns:
        str: A host IP address
    """
    try:
        device = proc_run(
            "route -n | grep ^0.0.0.0 | awk '{print $5,$8}' | sort -n | head -1 | awk '{print $2}'",
            shell=True, capture_output=True, text=True,
        ).stdout.strip()

        ip = proc_run(
            f"ip addr show dev {device} | grep inet | awk '{{print $2}}' | cut -d/ -f1",
            shell=True, capture_output=True, text=True,
        ).stdout.strip()

        if not ip:
            raise OSError

    except Exception:
        ip = "127.0.0.1"

    return ip


@lru_cache()
def fetch_app_log_filters(app_log_filters_path: (str, Path)) -> dict:
    """Fetch custom application's log filters

    This implementation fetches settings from a .toml file to be used to filter log messages
    with the engine processing of topics' app log messages.

    Args:
        app_log_filters_path (str, Path): The path to the .toml file.

    Returns:
        dict: As in: {'log_level': {'position': 2, 'accept': ['DEBUG', 'INFO'], 'clean_up_pattern': '\\[\\b|\\b]'}}
    """
    if not isinstance(app_log_filters_path, PosixPath):
        app_log_filters_path = Path(app_log_filters_path)

    app_log_filters = {}
    if app_log_filters_path.exists():
        with open(app_log_filters_path, "rb") as f:
            app_log_filters = load(f)

    return app_log_filters
