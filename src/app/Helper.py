#!/usr/bin/env python
"""My Python module

Description
"""
from functools import lru_cache
from subprocess import run as proc_run


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


if __name__ == "__main__":
    print(fetch_host_ip())
