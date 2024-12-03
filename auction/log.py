import atexit
import logging
import logging.config
import logging.handlers
import queue

from logging.handlers import QueueHandler, QueueListener
from pathlib import Path


logger = logging.getLogger("auction")

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s: %(message)s"},
        "detailed": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "detailed",
            "stream": "ext://sys.stderr",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/auction.log",
            "maxBytes": 10000000,
            "backupCount": 3,
        },
    },
    "loggers": {"root": {"level": "DEBUG", "handlers": ["stderr", "file"]}},
}


def setup_logging() -> None:
    logs = Path("logs")
    if not logs.exists():
        logs.mkdir()

    logging.config.dictConfig(log_config)

    que: queue.Queue = queue.Queue(-1)
    queue_handler = QueueHandler(que)
    handler = logging.StreamHandler()
    listener = QueueListener(que, handler)
    logger.addHandler(handler)

    if queue_handler is None:
        logger.error("unable to set queue handler")
        return

    listener.start()
    atexit.register(listener.stop)
