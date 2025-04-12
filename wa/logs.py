import logging
import logging.config

import uvicorn.logging
from asgi_correlation_id import CorrelationIdFilter

logger = logging.getLogger(__name__)


CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {
            "()": CorrelationIdFilter,
            "uuid_length": 8,
        },
    },
    "formatters": {
        "access": {
            "use_colors": True,
            "datefmt": r"%Y-%m-%d %H:%M:%S",
            "()": uvicorn.logging.AccessFormatter,
            "fmt": "%(levelprefix)s [%(asctime)s] [%(correlation_id)s] - %(request_line)s %(status_code)s",
        },
        "default": {
            "use_colors": True,
            "datefmt": r"%Y-%m-%d %H:%M:%S",
            "()": uvicorn.logging.DefaultFormatter,
            "fmt": "%(levelprefix)s [%(asctime)s] [%(correlation_id)s] [%(module)s:%(lineno)s] - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "filters": ["correlation_id"],
            "class": logging.StreamHandler,
        },
        "access": {
            "formatter": "access",
            "filters": ["correlation_id"],
            "class": logging.StreamHandler,
        },
    },
    "loggers": {
        "wa": {
            "level": logging.INFO,
            "handlers": ["default"],
        },
        "uvicorn.access": {
            "level": logging.INFO,
            "handlers": ["access"],
        },
        "openai": {
            "level": logging.INFO,
            "handlers": ["default"],
        },
        "httpx": {
            "level": logging.WARNING,
            "handlers": ["default"],
        },
        "pynamodb": {
            "level": logging.WARNING,
            "handlers": ["default"],
        },
    },
}


def init():
    logging.config.dictConfig(CONFIG)
