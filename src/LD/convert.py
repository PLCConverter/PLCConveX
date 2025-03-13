import logging
from Logs.colorLogger import ColorFormatter, get_color_logger

# Create a logger
logger = get_color_logger()

# Test the logger with different levels
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')