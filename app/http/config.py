from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.mongo import start_mongo, stop_mongo
from contextlib import asynccontextmanager

from .rest.v1 import (
   health_v1,
   auth_v1
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
    await start_mongo()


async def shutdown_event():
    await stop_mongo()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield
    await shutdown_event()

def configure_routes(app: FastAPI):
  app.include_router(health_v1)
  app.include_router(auth_v1)

def configure_app(app: FastAPI):

    configure_middlewares(app)
    configure_routes(app)
