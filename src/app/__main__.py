#!/usr/bin/env python3
from . import config as cfg
from .Logger import log


def main():
    topics = (cfg.HTTP_TOPIC_NAME, cfg.APP_TOPIC_NAME)


if __name__ == "__main__":
    main()
