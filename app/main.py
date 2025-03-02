from fastapi import FastAPI

from .http.config import configure_app, lifespan
from .core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        debug=settings.APP_DEBUG,
        version="0.0.1",
        title=settings.PROJECT_NAME,
        docs_url=f"/api/docs",
        redoc_url=f"/api/redocs",
        openapi_url=f"/api/docs/openapi.json",
        lifespan=lifespan
    )

    configure_app(app)

    return app


app = create_app()
