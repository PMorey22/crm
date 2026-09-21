import logging

from fastapi import FastAPI

from poc20.api.routes import router
from poc20.config import get_settings
from poc20.database import init_db


settings = get_settings()

logging.basicConfig(
    level=getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    ),
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Stateful AI-powered real-estate lead "
        "qualification and property matching service."
    ),
    version="2.0.0",
)

app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }