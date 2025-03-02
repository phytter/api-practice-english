from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .rest.v1 import (
   health_v1
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

def configure_routes(app: FastAPI):
  app.include_router(health_v1)

def configure_app(app: FastAPI):

    configure_middlewares(app)
    configure_routes(app)
