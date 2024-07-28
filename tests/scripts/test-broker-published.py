# !/usr/bin/env python
"""Script for consuming a sample of the produced (published) logs from the Broker"""
from datetime import datetime as _dt
from glob import glob
from pathlib import Path
from re import compile, match, sub

import pandas as pd
from pandas.core.series import Series

import app.config as cfg
from Broker import Consumer, log


def main():
    for topic in (cfg.HTTP_TOPIC_NAME, cfg.APP_TOPIC_NAME):
        consumer = Consumer(group=f"{cfg.LOG_NAME}-{topic}-tests", topics=topic)

        log.info(f"Start printing logs published to {topic=}")
        for data in consumer.consume():
            print(f"> {data[1].decode()}")


if __name__ == "__main__":
    main()
