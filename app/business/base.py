from fastapi.encoders import jsonable_encoder

from app.config.mongo import Mongo

__all__ = (
    "Mongo",
    "jsonable_encoder",
    "logger",
)
