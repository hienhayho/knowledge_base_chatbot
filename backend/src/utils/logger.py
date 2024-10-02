# This file contains the logger configuration for the application.

import sys
import click
import logging
from copy import copy
from typing import Literal

TRACE_LOG_LEVEL = 5


def get_formatted_logger(name: str, file_path: str | None = None):
    """
    Get a coloured logger.

    Args:
        name (str): The name of the logger.
        file_path (str | None): The path to the log file. Defaults to `None`.

    Returns:
        logging.Logger: The logger object.

    **Note:** Name is only use to prevent from being root logger.
    """
    logger = logging.getLogger(name=name)
    logger.setLevel(TRACE_LOG_LEVEL)

    if not logger.hasHandlers():
        stream_handler = logging.StreamHandler()
        stream_formatter = DefaultFormatter(
            "%(asctime)s | %(levelprefix)s - [%(filename)s %(funcName)s(%(lineno)d)] - %(message)s",
            datefmt="%Y/%m/%d  %H:%M:%S",
        )
        stream_handler.setFormatter(stream_formatter)
        logger.addHandler(stream_handler)

        if file_path:
            file_handler = logging.FileHandler(file_path)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)-8s - [%(filename)s %(funcName)s(%(lineno)d)] - %(message)s",
                datefmt="%Y/%m/%d - %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    return logger


class ColourizedFormatter(logging.Formatter):
    level_colors = {
        TRACE_LOG_LEVEL: "blue",
        logging.DEBUG: "cyan",
        logging.INFO: "green",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "magenta",
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: bool | None = None,
    ):
        """
        Initialize the formatter.

        Args:
            fmt (str | None): The format string. Defaults to `None`.
            datefmt (str | None): The date format string. Defaults to `None`.
            style (Literal["%", "{", "$"]): The style of the format string. Defaults to `%`.
            use_colors (bool | None): Whether to use colors. Defaults to `None`.
        """
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        """
        Colorize the level name.

        Args:
            level_name (str): The level name.
            level_no (int): The level number.

        Returns:
            str: The colorized level name.
        """
        color = self.level_colors.get(level_no, "reset")
        return click.style(str(level_name), fg=color)

    def color_message(self, message: str, level_no: int) -> str:
        """
        Colorize the message.

        Args:
            message (str): The message.
            level_no (int): The level number.

        Returns:
            str: The colorized message.
        """
        color = self.level_colors.get(level_no, "reset")
        return click.style(str(message), fg=color)

    def color_date(self, record: logging.LogRecord) -> str:
        """
        Apply green color to the date.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            str: The colorized date.
        """
        date_str = self.formatTime(record, self.datefmt)
        return click.style(date_str, fg="green")

    def should_use_colors(self) -> bool:
        """
        Check if colors should be used. Defaults to `True`.

        Returns:
            bool: Whether colors should be used.
        """
        return self.use_colors

    def formatMessage(self, record: logging.LogRecord) -> str:
        """
        Format the message.

        Args:
            record (logging.LogRecord): The log record.

        Returns:
            str: The formatted message.
        """
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        seperator = " " * (8 - len(recordcopy.levelname))

        if self.use_colors:
            levelname = self.color_level_name(levelname, recordcopy.levelno)
            recordcopy.msg = self.color_message(recordcopy.msg, recordcopy.levelno)
            recordcopy.__dict__["message"] = recordcopy.getMessage()
            recordcopy.asctime = self.color_date(recordcopy)

        recordcopy.__dict__["levelprefix"] = levelname + seperator
        return super().formatMessage(recordcopy)


class DefaultFormatter(ColourizedFormatter):
    def should_use_colors(self) -> bool:
        return sys.stderr.isatty()