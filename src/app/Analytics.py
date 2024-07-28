#!/usr/bin/env python
"""
My Python module
"""
from os import environ

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, from_json
from pyspark.sql.types import StructType, StructField, TimestampType, StringType

from . import config as cfg
from .Logger import log
from .Helper import fetch_host_ip


TOPICS = (cfg.HTTP_TOPIC_NAME, cfg.APP_TOPIC_NAME)


class Spark:
    """Engine class for Spark session with Kafka integration.

    This class instantiates the Kafka engine for processing data.
    It uses default values from a `.env` file, if specific values are not passed.
    The `.env` file is generated from the `env.json` template via a `make` command.

    Methods:
        start(): Start the Spark Session.
        subscribe(): Subscribe to the Kafka topics.
        process(): Start processing the topics' data.

    Examples:
        >>> e = Spark()
        >>> e.start()
        >>> e.subscribe()
        >>> e.process()
    """

    def __init__(self):
        log.debug("Spark engine init")
        self.engine = None
        self.__subscriptions = {}

    def start(self, app_name: str = cfg.APP_NAME) -> None:
        """Start the Spark Session."""
        environ["SPARK_LOCAL_IP"] = fetch_host_ip()
        self.engine = SparkSession.builder.appName(app_name) \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2") \
            .config("spark.log.level", "ERROR") \
            .getOrCreate()

        log.debug("Spark engine loaded")

    def subscribe(self, topics: iter = TOPICS) -> None:
        """Subscribe to the Kafka topics."""
        self.__subscriptions = {}

        for topic in topics:
            log.debug(f"Subscribe to {topic=} at {cfg.KAFKA_SERVER!r}")
            self.__subscriptions[topic] = self.engine.readStream.format("kafka") \
                .option("kafka.bootstrap.servers", cfg.KAFKA_SERVER) \
                .option("startingOffsets", "earliest") \
                .option("subscribe", topic) \
                .load()

    def process(self) -> SparkSession:
        """Start processing the topics' data."""
        for topic, spark_df in self.__subscriptions.items():
            topic = topic.split("-")[-1]

            spark_df = spark_df.selectExpr(
                "CAST(CAST(timestamp AS LONG) / 1000 AS timestamp) AS moment",
                "CAST(value AS STRING) AS value"
            ).select("moment", "value")
            spark_df = spark_df.filter(col("moment") > (pd.Timestamp.now() - pd.Timedelta(days=30)))
            print(f"Spark DF set for {topic}: {spark_df}")

            gdf = spark_df.groupBy(window(col("moment"), "1 minute")).count() \
                .withColumnRenamed("count", topic)

            q = gdf.writeStream.format("memory").queryName(topic).outputMode("complete").start()
            q.awaitTermination(10)

        log.info("Engine started")
        return self.engine
