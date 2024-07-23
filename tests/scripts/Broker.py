#!/usr/bin/env python
"""Broker manager for publishing messages"""
import logging as log
from json import dumps

from confluent_kafka import Producer as KafkaProducer

import app.config as cfg

KAFKA_SERVERS = {"bootstrap.servers": ",".join(cfg.KAFKA_SERVERS)}
TOPIC_PER_LOGS_DIR = {
    "/tmp/tests/http": "requests",
    "/tmp/tests/app": "responses",
}

log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(message)s')


class Producer:
    """Broker manager to publish messages to topics"""

    def __init__(self):
        """Initialize Publisher"""
        self.__producer = KafkaProducer(KAFKA_SERVERS)
        log.info(f'Connection established with: {", ".join(cfg.KAFKA_SERVERS)}')

        self.__counter = 0

    def produce(self, topic: str, data: (str, dict, iter), epoch_ms: float) -> None:
        """Publishes a message to a specified topic

        Args:
            topic (str): The name of the topic to publish to
            data (str, dict, iter): The message to be published (can be string, dictionary, or iterable)
            epoch_ms (float): The epoch timestamp, as in "1721666946" or "1721666946.053233"
        """
        self.__producer.poll(timeout=0)  # fetch previous calls

        if isinstance(data, (str, dict)):
            data = [data]

        for d in data:
            d = dumps(d, separators=(',', ':'), sort_keys=True).encode() if isinstance(d, dict) else d.encode()

            self.__producer.produce(
                topic=topic,
                value=d,
                timestamp=int(epoch_ms * 1000000),
                callback=self.__report,
            )
            self.__counter += 1

        self.__producer.poll(timeout=9)
        self.__producer.flush(timeout=3)

    @staticmethod
    def __report(error, message):
        if error:
            log.error(f"{error}: Not delivered: {message}")
