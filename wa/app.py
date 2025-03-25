import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def create() -> FastAPI:
    from wa.lifespan import lifespan
    from wa.routes import router

    logger.info("Creating FastAPI app")
    app = FastAPI(lifespan=lifespan, debug=True)
    app.include_router(router)
    app.add_middleware(CorrelationIdMiddleware)
    return app
