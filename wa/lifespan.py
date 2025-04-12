import contextlib
import logging
from typing import AsyncGenerator

from fastapi import FastAPI

import wa.dynamo
import wa.logs
from wa.config import Config

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting server...")

    cfg = Config()  # type: ignore
    wa.logs.init()
    wa.dynamo.init(cfg)

    logger.info("Finished starting server")
    yield  # server runs
    logger.info("Shutting down server")
    logger.info("Finished shutting down server")
