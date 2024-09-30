import logging
from typing import List

from src.const.config import GlobalConfig

from .handlers import Handlers


class LogHandler(object):
    def __init__(self):
        self.available_handlers: List = Handlers().get_handlers()

    def get_logger(self, logger_name):
        logger = logging.getLogger(logger_name)
        logger.setLevel(GlobalConfig.LOG_LEVEL)
        if logger.hasHandlers():
            logger.handlers.clear()
        for handler in self.available_handlers:
            logger.addHandler(handler)
        logger.propagate = False
        return logger