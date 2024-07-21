#!/usr/bin/env python
"""Script for publishing mocked logs

This script publishes mocked logs, created from `make test-create-mocked-logs`, into a Kafka local service.
On its first run, this script will collect logs from the 3 more recent http log files from the mocked logs directories,
and publish these logs to the Broker. Every next run will collect and publish from the last published log.

This script uses a state file to try to avoid publishing duplications.
The script will fetch all HTTP and API files, no matter how old the logs are. If the script is interrupted,
it will use the state file to know where to resume from. If older logs need to be streamed,
the recommendations is to rename or remove the log files' directory.

The pattern for http log lines is set in the `HTTP_LOG_PATTERN` list.
Every existing string separated by spaces must have a related column name in that list.
Some names have special processing:
- "ignore" ignores the related value
- "timestamp" and "timezone" accepts only datetime-related characters
- "<column-name>:quoted" informs about values with spaces that must not be split
"""
from datetime import datetime as _dt
from concurrent.futures import ThreadPoolExecutor, wait
from gc import collect as collect_garbage
from glob import glob
from json import dumps
from pathlib import Path
from re import sub

import pandas as pd
from confluent_kafka import (
    Producer as KafkaProducer,
    KafkaException,  # noqa
)

import app.config as cfg
from Broker import Producer


# 10.1.1.17 - calasans@home.homenet [21/Jul/2024:11:28:04 +01:00] "PUT /users HTTP/9.9" 201 999
# 203.0.113.73 - - [21/Jul/2024:11:28:04 +01:00] "GET /?page=x HTTP/9.9" 201 999
HTTP_LOG_PATTERN = ["ip", "ignore", "user", "timestamp", "timezone", "request:quoted", "status", "size"]
STRIP = {"timestamp": r"[", "timezone": r"]"}

KAFKA_SERVERS = {"bootstrap.servers": ",".join(cfg.KAFKA_SERVERS)}
TOPIC_PER_LOGS_DIR = {
    "/tmp/tests/http": "requests",
    "/tmp/tests/app": "responses",
}


class LogPublisher:
    def __init__(self, logs_dir: str, topic: str):
        self.__logs_dir = logs_dir
        self.__topic = topic
        self.__state_file = Path(f"{logs_dir}/.last_published_state_file")

        self.__last_published_log_epoch = self.__fetch_last_published_log_epoch()
        self.__candidate_log_files = self.__update_candidate_log_files()

        print("Publish logs younger than {}".format(
            pd.to_datetime(self.__last_published_log_epoch, unit="s", utc=True)
        ))

    @property
    def candidate_log_files(self) -> iter:
        for f in sorted(self.__candidate_log_files):
            yield f.as_posix()

    def publish(self) -> None:
        published = {}
        last_published_log_epoch = 0

        for f in sorted(self.__candidate_log_files, reverse=True):
            print(f"- Fetch log lines from {f.as_posix()}")

            for data in self.__fetch_log_lines(f):
                # p.produce(topic=topic, key=key, data=msg, epoch_ms=msg_epoch_ms)
                print(data)  # todo: check data, publish, update published, update last_published_log_epoch if greater
                pass

                if f.as_posix() not in published:
                    published[f.as_posix()] = 0

        if not published:
            print("No candidate log files or all logs already sent")
            return

        if last_published_log_epoch > self.__last_published_log_epoch:
            self.__last_published_log_epoch = last_published_log_epoch
            self.__store_last_published_log_timestamp()

        print("Published to ")

    def __fetch_last_published_log_epoch(self) -> float:
        ts = 0.0

        if self.__state_file.exists():
            with open(self.__state_file) as f:
                ts = float(f.read().strip())

        return ts

    def __update_candidate_log_files(self) -> list:
        files = []

        for log_file in sorted(glob(f"{self.__logs_dir}/*log*")):
            f = Path(log_file)

            if f.is_file() and f.stat().st_mtime >= self.__last_published_log_epoch:
                files.append(f)

            if len(files) > 2:
                break

        return files

    def __fetch_log_lines(self, source: Path) -> iter:
        targeted_cols = [i for i, col in enumerate(HTTP_LOG_PATTERN) if col != "ignore"]
        ignored_cols = list(set(range(len(HTTP_LOG_PATTERN))) - set(targeted_cols))
        quoted_cols = [c for i, c in enumerate(HTTP_LOG_PATTERN) if ":quoted" in c and i not in ignored_cols]
        temporary_cols = []

        df = pd.read_csv(source, sep=" ", skipinitialspace=True, header=None, engine="python", usecols=targeted_cols)

        try:
            df.columns = [HTTP_LOG_PATTERN[i] for i in targeted_cols]

        except ValueError as e:
            if "Length mismatch" in str(e):
                print(f"Mismatch between fetched logs and expected columns:\n{HTTP_LOG_PATTERN}\n{df.head(3)}")
            return

        parsed = pd.to_datetime(
            df["timestamp"].str.strip(STRIP.get("timestamp")) + df["timezone"].str.strip(STRIP.get("timezone")),
            format='%d/%b/%Y:%H:%M:%S%z'
        )

        new_temp_col = HTTP_LOG_PATTERN.index("timezone") + 1
        df.insert(new_temp_col, "datetime", parsed)
        temporary_cols.append(new_temp_col)
        # print(df)

        last_published_datetime = pd.to_datetime(self.__last_published_log_epoch, unit="s", utc = True)
        # print(last_published_datetime)
        filtered_df = df[df["datetime"].to_numpy() > last_published_datetime]

        del df
        collect_garbage()

        for _, tupled_row in filtered_df.iterrows():
            row = []
            row_datetime = tupled_row.get("datetime", tupled_row.get("timestamp"))

            for i, tupled_data in enumerate(tupled_row.items()):
                if i in temporary_cols:
                    continue

                v = f'\"{str(tupled_data[1])}\"' if tupled_data[0] in quoted_cols else str(tupled_data[1])
                row.append(v)

            for i in sorted(ignored_cols, reverse=True):
                row.insert(i, "-")

            yield row_datetime, " ".join(row)

    def __store_last_published_log_timestamp(self):
        pass


def run():
    for logs_dir, topic in TOPIC_PER_LOGS_DIR.items():
        if topic == "responses": continue
        publisher = LogPublisher(logs_dir, topic)
        publisher.publish()


if __name__ == "__main__":
    run()
