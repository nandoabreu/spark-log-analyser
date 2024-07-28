# !/usr/bin/env python
"""Script for consuming a sample of the produced (published) logs from the Broker"""
from re import sub

import app.config as cfg
from app.Helper import fetch_app_log_filters
from Broker import Consumer, log


def main():
    app_log_filters = {}

    for topic in (cfg.HTTP_TOPIC_NAME, cfg.APP_TOPIC_NAME):
        consumer = Consumer(group=f"{cfg.LOG_NAME}-{topic}-tests", topics=topic)

        log.info(f"Start printing logs published to {topic=}")
        for data in consumer.consume():
            log_str = data[1].decode()
            if len(log_str) > 100:
                log_str = f"{log_str[:98]}..."

            print(f"> {log_str}")

            log_list = log_str.split()

            if not app_log_filters and topic in (cfg.APP_TOPIC_NAME,):
                app_log_filters = fetch_app_log_filters(cfg.APP_LOG_FILTERS_TOML_PATH)
                filters = app_log_filters.get("log_level", {})
                position = filters.get("position")
                accept = filters.get("accept")
                clean_up_pattern = filters.get("clean_up_pattern")

                if position:
                    log_level = sub(clean_up_pattern, "", log_list[position])
                    if not accept or log_level in accept:
                        print(f"  - Matches filtered log level: {log_level}")


if __name__ == "__main__":
    main()
