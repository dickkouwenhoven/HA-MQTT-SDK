"""
Centralized logger utility.
Supports dual-mode logging: uses existing logger if available.
"""

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
	logger = logging.getLogger(name)
	if logger.handlers:
		return logger
	logger.setLevel(level)
	handler = logging.StreamHandler(sys.stdout)
	formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	return logger

def get_logger(name: str) -> logging.Logger:
	return setup_logger(name)
