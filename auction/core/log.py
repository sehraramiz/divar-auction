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
    "filters": {
        "correlation_id": {
            "()": "asgi_correlation_id.CorrelationIdFilter",
            "uuid_length": 32,
            "default_value": "-",
        },
    },
    "formatters": {
        "simple": {"format": "%(levelname)s: %(message)s"},
        "detailed": {
            "format": (
                "%(levelname)s|[%(correlation_id)s]|%(module)s|"
                "L%(lineno)d %(asctime)s: %(message)s"
            ),
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": {
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "detailed",
            "stream": "ext://sys.stderr",
            "filters": ["correlation_id"],
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
            "filters": ["correlation_id"],
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/auction.log",
            "maxBytes": 10000000,
            "backupCount": 3,
            "filters": ["correlation_id"],
        },
    },
    "loggers": {"root": {"level": "DEBUG", "handlers": ["stderr", "file", "stdout"]}},
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
