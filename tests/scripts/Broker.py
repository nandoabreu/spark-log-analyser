#!/usr/bin/env python
"""Broker manager for publishing messages"""
import logging as log
from concurrent.futures import ThreadPoolExecutor
from json import dumps
from os import cpu_count

from confluent_kafka import (
    Consumer as KafkaConsumer,
    Producer as KafkaProducer,
    KafkaError,
    KafkaException,
)

import app.config as cfg

KAFKA_SERVER = {"bootstrap.servers": cfg.KAFKA_SERVER}
TOPIC_PER_LOGS_DIR = {
    "/tmp/tests/http": cfg.HTTP_TOPIC_NAME,
    "/tmp/tests/app": cfg.APP_TOPIC_NAME,
}

# noinspection SpellCheckingInspection
log.basicConfig(level=cfg.LOG_LEVEL, format='%(asctime)s [%(levelname)s] %(message)s')


class Producer:
    """Broker manager to publish messages to topics"""

    def __init__(self):
        """Initialize Publisher"""
        self.__producer = KafkaProducer(KAFKA_SERVER)
        log.debug(f'Connection established with: {cfg.KAFKA_SERVER!r}')

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


class Consumer:
    """Broker manager to consume messages from topics"""

    def __init__(self, group: str = "my_group", topics: (str, iter) = "my_topic"):
        """Initialize Consumer

        Initialize the Broker consumer object.

        Args:
            group (str): the client's group (topics offsets are fixed for the group)
            topics (str, iter): One os more names of topics to consume from.
        """
        log.debug(f'Broker consumer init on id={id(self)}')

        if isinstance(topics, (str, bytes)):
            topics = set(topics.split(","))
        if not isinstance(topics, list):
            topics = list(topics)

        self.__consumer = KafkaConsumer(KAFKA_SERVER | {
            "auto.offset.reset": "earliest",
            "group.id": group,
        })
        log.debug(f'Connection established with: {cfg.KAFKA_SERVER!r}')

        log.debug(f"Subscribe to topics: {topics}")
        self.__consumer.subscribe(topics=topics)

    def consume(self, messages: int = 3) -> iter:
        """Consumes messages from specified topics

        Args:
            messages (int): The number os messages to fetch from the topic.

        Yields:
            tuple: Containing the epoch of the publication and the message itself.

        Raises:
            KafkaException: For existent topic, end of topic partition queue or data error
        """
        executor = ThreadPoolExecutor(max_workers=cpu_count())

        for i in range(messages):
            data = self.__consumer.poll(timeout=5)

            if data:
                if data.error():
                    err = None
                    if data.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                        err = "Topic not yet created: try to produce first"
                    elif data.error().code() == KafkaError._PARTITION_EOF:
                        err = f"End of topic {data.topic()!r}: partition {data.partition()}; offset {data.offset()}"
                    elif data.error():
                        err = data.error()

                    self.__consumer.close()
                    raise KafkaException(err)

                executor.submit(self.__consumer.commit, data)
                yield data.timestamp()[1] // 1_000_000, data.value()

        executor.shutdown(wait=False)
