import logging
from enum import Enum

LOG_FORMAT_DEBUG = "%(levelname)s-%(message)s-%(pathname)s-%(funcName)s-%(lineno)d"

class LogLevels(Enum):
    debug = logging.DEBUG
    info = logging.INFO
    warn = logging.WARNING
    error = logging.ERROR

def configure_logging(log_level: str = LogLevels.error.value):
    log_level = str(log_level).upper()
    log_levels = [level.value for level in LogLevels]

    if log_level not in log_levels:
        logging.basicConfig(level=LogLevels.error.value)
        return
    
    if log_level == LogLevels.debug:
        logging.basicConfig(level=log_level, format=LOG_FORMAT_DEBUG)
    
    logging.basicConfig(level=log_level)