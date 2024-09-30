import logging
import sys
from logging.handlers import SocketHandler, TimedRotatingFileHandler
from pathlib import Path

from src.constants import GlobalConfig


class Handlers:
    def __init__(self):
        self.formatter = logging.Formatter(GlobalConfig.FORMATTER)
        self.log_filename = Path().joinpath(GlobalConfig.APP_CONFIG.LOGS_DIR, GlobalConfig.FILENAME)
        self.rotation = GlobalConfig.ROTATION

    def get_console_handler(self):
        console_handler = logging.StreamHandler(sys.stdout.flush())
        console_handler.setFormatter(self.formatter)
        return console_handler

    def get_file_handler(self):
        file_handler = TimedRotatingFileHandler(self.log_filename, when=self.rotation)
        file_handler.setFormatter(self.formatter)
        return file_handler

    def get_socket_handler(self):
        socket_handler = SocketHandler("127.0.0.1", 19996)  # default listening address
        return socket_handler

    def get_handlers(self):
        return [self.get_console_handler(), self.get_file_handler(), self.get_socket_handler()]