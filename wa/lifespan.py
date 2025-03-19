import contextlib
import logging

from fastapi import FastAPI

import wa.config
import wa.dynamo
import wa.logs
import wa.models
import wa.whatsapp

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting server...")

    cfg = wa.config.Config()  # type: ignore
    wa.logs.init()
    wa.dynamo.init(cfg)

    logger.info("Finished starting server")
    yield  # server runs
    logger.info("Shutting down server")
    logger.info("Finished shutting down server")
