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
from gc import collect as collect_garbage
from glob import glob
from pathlib import Path
from re import compile, match

import pandas as pd

from Broker import Producer, log

LOGS_DIR = "/tmp/tests/app"
BROKER_CONN_SETTINGS = {"bootstrap.servers": ",".join(cfg.KAFKA_SERVERS)}
BROKER_TOPIC = "responses"
TIMESTAMP_PATTERNS = {
    "%d/%b/%Y": "[1-3][0-9]/[A-z]{3}/[12][0-9][0-9][0-9]",
    "%Y-%m-%d": "[12][0-9][0-9][0-9]-[01][0-9]-[1-3][0-9]",
    "%H:%M": "[012]?[0-9](:[0-5][0-9]){1}",
}
TIMESTAMP_PATTERNS["%T"] = TIMESTAMP_PATTERNS["%H:%M"].replace("{1}", "{2}")
TIMESTAMP_PATTERNS["%d/%b/%Y:%H:%M:%S"] = "{}:{}".format(TIMESTAMP_PATTERNS["%d/%b/%Y"], TIMESTAMP_PATTERNS["%T"])
TIMESTAMP_PATTERNS["%z"] = "[+-]{}".format(TIMESTAMP_PATTERNS["%H:%M"])


class LogPublisher:
    def __init__(self, logs_dir: str, topic: str):
        self.__logs_dir = logs_dir
        self.__state_file = Path(f"{logs_dir}/.last_published_state_file")
        self.__topic = topic
        self.__broker = None

        self.last_published_log_epoch = self.__fetch_last_published_log_epoch()
        self.__candidate_log_files = self.update_candidate_log_files()

        log.debug("Publish logs younger than {:%F %T}".format(
            pd.to_datetime(self.last_published_log_epoch, unit="s")
        ))

    @property
    def candidate_log_files(self) -> tuple:
        return tuple(f.as_posix() for f in sorted(self.__candidate_log_files))

    def publish(self) -> None:
        published = {}

        for f in sorted(self.__candidate_log_files, reverse=True):
            path = f.as_posix()
            log.debug(f"Fetch log lines from {path}")

            for log_epoch, log_str in self.fetch_log_lines(f):
                if self.last_published_log_epoch > log_epoch:
                    continue

                if not self.__broker:
                    self.__broker = Producer()

                self.__broker.produce(topic=self.__topic, data=log_str, epoch_ms=log_epoch)

                if path not in published:
                    published[path] = {"count": 0, "last_log_epoch": 0.0}

                published[path]["count"] += 1
                if log_epoch > published[path]["last_log_epoch"]:
                    published[path]["last_log_epoch"] = log_epoch

        if not published:
            log.info("No candidate log files or all logs already sent")
            self.last_published_log_epoch = _dt.now().timestamp()
            self.__store_last_published_log_epoch()
            return

        overall_last_log_epoch = max([published[path]["last_log_epoch"] for path in published])
        overall_log_publish_count = sum([published[path]["count"] for path in published])
        log.info(f"Published messages to broker: {overall_log_publish_count}")

        if overall_last_log_epoch > self.last_published_log_epoch:
            self.last_published_log_epoch = overall_last_log_epoch
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
            - Timestamp (float): The epoch of the log line or -1 if not parsed
            - Log line (str): The raw log line
        """
        lines = []
        with open(source) as f:
            lines = f.readlines()

        if not lines:
            return

        df = pd.DataFrame([l.strip().split()[:5] + [l.strip()] for l in lines])

        timestamp_patterns = [compile(t) for t in TIMESTAMP_PATTERNS.values()]

        datetime_cols = []
        for i, value in enumerate(df.iloc[0]):
            for pattern in timestamp_patterns:
                if match(pattern, str(value)):
                    datetime_cols.append(i)

        if not datetime_cols:
            log.error(f"Unable to interpret a datetime patten from the first line of {source.as_posix()}")
            return

        df[0] = pd.to_datetime(df[datetime_cols].astype(str).agg(' '.join, axis="columns"))
        df.drop(df.columns[1:-1], axis="columns", inplace=True)

        last_published_datetime = pd.to_datetime(self.last_published_log_epoch, unit="s")
        df = df[df[0] > last_published_datetime]

        for row in df.values:
            yield row[0].timestamp(), row[1]

    def __store_last_published_log_epoch(self):
        with open(self.__state_file, "w") as f:
            f.write(str(self.last_published_log_epoch))

        log.info("State persisted")


def run():
    publisher = LogPublisher(LOGS_DIR, BROKER_TOPIC)
    publisher.publish()


if __name__ == "__main__":
    run()
