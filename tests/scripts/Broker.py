#!/usr/bin/env python
"""Broker manager for publishing messages"""
from datetime import datetime as _dt
from concurrent.futures import ThreadPoolExecutor, wait
from json import dumps

from confluent_kafka import (
    Producer as KafkaProducer,
    KafkaException,  # noqa
)

import app.config as cfg

KAFKA_SERVERS = {"bootstrap.servers": ",".join(cfg.KAFKA_SERVERS)}
TOPIC_PER_LOGS_DIR = {
    "/tmp/tests/http": "requests",
    "/tmp/tests/app": "responses",
}


class Producer:
    """Broker manager to publish messages to topics"""

    def __init__(self):
        """Initialize Publisher"""
        self.__producer = KafkaProducer(KAFKA_SERVERS)
        print(f"Connected to: {cfg.KAFKA_SERVERS}")

        self.__counter = 0

    def produce(self, data: (dict, iter), topic: str = "my_topic", key=None, epoch_ms=None):
        self.__producer.poll(timeout=0)  # fetch previous calls

        if isinstance(data, dict):
            data = [data]

        for d in data:
            if not isinstance(d, dict):
                print(f"Skip message (not dict): {d}")
                continue

            now = _dt.utcnow()
            self.__producer.produce(
                timestamp=epoch_ms,
                topic=topic,
                headers=[],
                key=key.encode() if key else None,
                value=dumps(d, separators=(',', ':'), sort_keys=True).encode(),
                callback=self.__report,
            )
            self.__counter += 1

        self.__producer.poll(timeout=9)
        self.__producer.flush(timeout=3)

    @staticmethod
    def __report(error, message=None):
        if error:
            print(f"Message not delivered: {error}")
        # else:
        #     print('Delivered to {!r} at partition {}: {}'.format(
        #         message.topic(), message.partition(), message.value().decode()
        #     ))
