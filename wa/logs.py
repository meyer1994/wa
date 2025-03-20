import logging
import logging.config

import uvicorn.logging

logger = logging.getLogger(__name__)


CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "access": {
            "()": uvicorn.logging.AccessFormatter,
            "fmt": "%(levelprefix)s [%(asctime)s]  - %(request_line)s %(status_code)s",
            "datefmt": r"%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
        "default": {
            "()": uvicorn.logging.DefaultFormatter,
            "fmt": "%(levelprefix)s [%(asctime)s] [%(module)s:%(lineno)s] - %(message)s",
            "datefmt": r"%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": logging.StreamHandler,
        },
        "access": {
            "formatter": "access",
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
        "pynamodb": {
            "level": logging.INFO,
            "handlers": ["default"],
        },
    },
}


def init():
    logging.config.dictConfig(CONFIG)
