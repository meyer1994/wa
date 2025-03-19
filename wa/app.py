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
    wa.logs.init()

    logger.info("Starting server...")
    wa.dynamo.WhatsAppItem.create_table(
        wait=True,
        write_capacity_units=1,
        read_capacity_units=1,
    )
    wa.dynamo.MessageText.create_table(
        wait=True,
        write_capacity_units=1,
        read_capacity_units=1,
    )
    logger.info("Finished starting server")

    yield

    logger.info("Shutting down server")
    logger.info("Finished shutting down server")


def create() -> FastAPI:
    from wa.routes import router

    app = FastAPI(lifespan=lifespan, debug=True)
    app.include_router(router)
    return app
