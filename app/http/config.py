from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import (
    start_mongo,
    stop_mongo,
    start_logging,
    stop_logging,
    start_http_client,
    stop_http_client,
    start_audio_processor,
    stop_audio_processor
)
from contextlib import asynccontextmanager

from .rest.v1 import (
   health_v1,
   auth_v1,
   movie_v1,
   dialogue_v1,
)

def configure_middlewares(app: FastAPI):
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
      expose_headers=["X-Request-ID", "X-Request-Time"],
      max_age=600,  # Seconds
  )

async def startup_event():
    start_logging()
    await start_mongo()
    await start_http_client()
    start_audio_processor()

async def shutdown_event():
    await stop_mongo()
    await stop_http_client()
    stop_audio_processor()
    await stop_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield
    await shutdown_event()

def configure_routes(app: FastAPI):
  app.include_router(health_v1)
  app.include_router(auth_v1)
  app.include_router(movie_v1)
  app.include_router(dialogue_v1)

def configure_app(app: FastAPI):

    configure_middlewares(app)
    configure_routes(app)
