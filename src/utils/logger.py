import logging
import sys
from pathlib import Path

class MyLogger:
    """
    Simple wrapper around logging.Logger.
    Usage: from logger import logger
         logger.info("message")
    """

    def __init__(self, name: str = "OncoAgents", level: int = logging.INFO, logfile: str | None = None):
        self._logger = logging.getLogger(name)

        # Avoid adding duplicate handlers on repeated imports
        if not self._logger.handlers:
            self._logger.setLevel(level)
            fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S")

            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(level)
            ch.setFormatter(fmt)
            self._logger.addHandler(ch)

            if logfile:
                Path(logfile).parent.mkdir(parents=True, exist_ok=True)
                fh = logging.FileHandler(logfile)
                fh.setLevel(level)
                fh.setFormatter(fmt)
                self._logger.addHandler(fh)

    # Convenience passthrough methods
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    # Accept both warning and deprecated warn
    warn = warning

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)

    def setLevel(self, level):
        self._logger.setLevel(level)

    def addHandler(self, handler):
        self._logger.addHandler(handler)

    # Delegate any other attributes to underlying logger
    def __getattr__(self, name):
        return getattr(self._logger, name)

logger = MyLogger()
