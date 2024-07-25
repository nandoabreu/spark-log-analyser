#!/usr/bin/env python
"""Script for publishing mocked logs

This script publishes mocked logs, created from `make test-create-mocked-logs`, to a local broker service.
On its first run, this script will collect logs from the 3 most recent log files from the mocked logs directories,
and publish these logs to the broker. Every next run will collect and publish from the last published log.

This script uses a state file to try to avoid publishing duplications.
The script will fetch no matter how old the logs are. If the script is interrupted,
it will use the state file to know where to resume from. If older logs need to be streamed,
the recommendations is to rename or remove the log files' directory.
"""
from datetime import datetime as _dt
from glob import glob
from pathlib import Path
from re import compile, match, sub

import pandas as pd
from pandas.core.series import Series

from Broker import TOPIC_PER_LOGS_DIR, Producer, log

TIMESTAMP_PATTERNS = {
    "%d/%b/%Y": "[1-3][0-9]/[A-z]{3}/[12][0-9][0-9][0-9]",
    "%Y-%m-%d": "[12][0-9][0-9][0-9]-[01][0-9]-[1-3][0-9]",
    "%H:%M:%S": "[012]?[0-9](:[0-5][0-9]){2}",
}
TIMESTAMP_PATTERNS["%d/%b/%Y:%H:%M:%S"] = "{}:{}".format(TIMESTAMP_PATTERNS["%d/%b/%Y"], TIMESTAMP_PATTERNS["%H:%M:%S"])
TIMESTAMP_PATTERNS["%H:%M"] = TIMESTAMP_PATTERNS["%H:%M:%S"].replace("{2}", "?")
TIMESTAMP_PATTERNS["%z"] = "[+-]{}".format(TIMESTAMP_PATTERNS["%H:%M"])


class LogPublisher:
    def __init__(self, logs_dir: str, topic: str):
        if not Path(logs_dir).is_dir():
            msg = f"Not a directory: {logs_dir}"
            log.error(msg)
            raise ValueError(msg)

        self.__logs_dir = logs_dir
        self.__state_file = Path(f"{logs_dir}/.last_published_state_file")
        self.__topic = topic
        self.__broker = None

        self.last_published_log_epoch = self.__fetch_last_published_log_epoch()
        self.__candidate_log_files = self.update_candidate_log_files()

        self.__timestamp_patterns = {s: compile(rf"^{p}$") for s, p in TIMESTAMP_PATTERNS.items()}
        self.__datetime_columns_patterns = None

        log.debug("Publish logs younger than {:%F %T UTC}".format(
            pd.to_datetime(self.last_published_log_epoch, unit="s")
        ))

    @property
    def candidate_log_files(self) -> tuple:
        return tuple(f.as_posix() for f in sorted(self.__candidate_log_files))

    def publish(self) -> None:
        published = {
            "first_in_batch": None,
            "youngest_log_epoch": 0.0,
            "count": 0,
        }

        for f in sorted(self.__candidate_log_files, reverse=True):
            path = f.as_posix()
            log.debug(f"Fetch log lines from {path}")

            for log_epoch, log_str in self.fetch_log_lines(f):
                # log.debug("> Fetched: ({}, {!r})".format(log_epoch, log_str))

                if self.last_published_log_epoch > log_epoch:
                    continue

                if not self.__broker:
                    self.__broker = Producer()

                self.__broker.produce(topic=self.__topic, data=log_str, epoch_ms=log_epoch)

                if not published["first_in_batch"]:
                    published["first_in_batch"] = (log_epoch, log_str)
                published["count"] += 1

                if log_epoch > published["youngest_log_epoch"]:
                    published["youngest_log_epoch"] = log_epoch

        if not published["count"]:
            log.info("No candidate log files or all logs already sent")
            self.last_published_log_epoch = _dt.now().timestamp()
            self.__store_last_published_log_epoch()
            return

        log.info("Published messages to broker: {}".format(published["count"]))
        log.info("First published in batch: {}".format(published["first_in_batch"]))
        log.info("Last published in batch: {}".format((log_epoch, log_str)))

        if published["youngest_log_epoch"] > self.last_published_log_epoch:
            self.last_published_log_epoch = published["youngest_log_epoch"]
            self.__store_last_published_log_epoch()

    def __fetch_last_published_log_epoch(self) -> float:
        ts = 0.0

        if self.__state_file.exists():
            with open(self.__state_file) as f:
                ts = float(f.read().strip())

        return ts

    def update_candidate_log_files(self) -> list:
        files = []

        for log_file in sorted(glob(f"{self.__logs_dir}/*log*")):
            if len(files) > 2:  # Fetch only the 3 most recent logs
                break

            f = Path(log_file)

            if f.is_file() and f.stat().st_mtime >= self.last_published_log_epoch:
                files.append(f)

        return files

    def fetch_log_lines(self, source: Path) -> iter:
        """Parses log lines from a given source file path

        Args:
            source (Path): Path to the log file

        Returns:
            Generator of tuples. Each tuple contains:
            - Epoch (int, float): The epoch of the log line or -1 if not parsed
            - Log line (str): The raw log line
        """
        lines = []
        with open(source) as f:
            lines = f.readlines()

        if not lines:
            return

        df = pd.DataFrame([l.strip().split()[:5] + [l.strip()] for l in lines])
        if not self.__datetime_columns_patterns:
            self.__parse_datetime_patterns(df.iloc[0])

        if not self.__datetime_columns_patterns:
            log.error(f"Unable to interpret a datetime patten from the first line of {source.as_posix()}")
            return

        df[0] = pd.to_datetime(
            df[
                [int(c) for c in self.__datetime_columns_patterns]
            ]
            .astype(str)
            .agg(' '.join, axis="columns")
            .str.replace(r"[^\w/:+-., ]", "", regex=True),
            format=" ".join(self.__datetime_columns_patterns.values()),
        ).astype('int64') // 10 ** 9  # cast datetime collection as epoch
        df.drop(df.columns[1:-1], axis="columns", inplace=True)

        df = df[df[0] > self.last_published_log_epoch]

        for row in df.values:
            yield row

    def __parse_datetime_patterns(self, df_row: Series) -> None:
        log.debug(f'Try to interpret datetime patterns from {" ".join(df_row.astype(str))!r}')
        datetime_cols = {}

        for i, value in enumerate(df_row):
            value = sub(r"[^\w/:+-.,]", "", value)
            if not value:
                continue

            for s, pattern in self.__timestamp_patterns.items():
                if match(pattern, str(value)):
                    log.debug(f"Datetime [sub]string {value} matches pattern {pattern}")
                    datetime_cols[str(i)] = s
                    break

        self.__datetime_columns_patterns = datetime_cols
        log.debug(f"Set datetime patterns for topic {self.__topic!r}: {self.__datetime_columns_patterns}")

    def __store_last_published_log_epoch(self):
        with open(self.__state_file, "w") as f:
            f.write(str(self.last_published_log_epoch))

        log.info("State persisted")


def run():
    for logs_dir, topic in TOPIC_PER_LOGS_DIR.items():
        publisher = LogPublisher(logs_dir, topic)
        publisher.publish()


if __name__ == "__main__":
    run()
