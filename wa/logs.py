import logging
import logging.config
import sys

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
            "stream": sys.stderr,
        },
        "access": {
            "formatter": "access",
            "filters": ["correlation_id"],
            "class": logging.StreamHandler,
            "stream": sys.stderr,
        },
    },
    "loggers": {
        "wa": {
            "propagate": False,
            "level": logging.DEBUG,
            "handlers": ["default"],
        },
        "uvicorn.access": {
            "propagate": False,
            "level": logging.INFO,
            "handlers": ["access"],
        },
        # "openai": {
        #     "level": logging.DEBUG,
        #     "handlers": ["default"],
        #     "propagate": False,
        # },
        "pynamodb": {
            "level": logging.DEBUG,
            "handlers": ["default"],
            "propagate": False,
        },
    },
}


def init():
    logging.config.dictConfig(CONFIG)
