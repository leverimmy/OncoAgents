import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MyLogger:
    def __init__(
        self,
        name: str = "OncoAgents",
        level: int = logging.INFO,
        log_dir: str | None = None,
    ):
        self._logger = logging.getLogger(name)

        # Avoid adding duplicate handlers on repeated imports
        if not self._logger.handlers:
            self._logger.setLevel(level)

            fmt = logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )

            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(level)
            ch.setFormatter(fmt)
            self._logger.addHandler(ch)

            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

                timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                log_filename = f"{name}_{timestamp}.log"
                log_path = os.path.join(log_dir, log_filename)

                fh = logging.FileHandler(log_path, encoding="utf-8")
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

logger = MyLogger(
    name="OncoAgents",
    log_dir=os.getenv("LOGGING_FILE_DIR", "logs"),
)
