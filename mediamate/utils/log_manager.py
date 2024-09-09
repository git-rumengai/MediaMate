"""
This module defines a LogManager class for logging configuration and logger retrieval.
"""
import sys
import io
import logging
from mediamate.config import config


class Utf8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        # Default to sys.stdout if no stream is provided
        stream = stream or sys.stdout
        super().__init__(stream=io.TextIOWrapper(stream.buffer, encoding='utf-8'))


class LogManager:
    """
    Manages logging settings and provides loggers.

    Initializes the root logger and adds a console handler.
    """
    def __init__(self):
        """ Sets up the root logger and its console handler. """
        console_handler = Utf8StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s:%(lineno)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        config.ROOT_LOGGER.addHandler(console_handler)

    @staticmethod
    def get_logger(name):
        """
        Gets a child logger based on the given name.

        Args:
            name (str): Name for the child logger.

        Returns:
            logging.Logger: The child logger instance.
        """
        relative_path = name.replace(config.PROJECT_DIR, '')
        relative_path = relative_path.lstrip('/').lstrip('\\').replace('.py', '')
        return config.ROOT_LOGGER.getChild(relative_path)


log_manager = LogManager()
# 通过 `__all__` 控制公共接口
__all__ = ['log_manager']


if __name__ == "__main__":
    logger = log_manager.get_logger(__file__)
    logger.info("This is an info message.")
    logger.error("This is an error message.")
