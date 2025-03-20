from fastapi.encoders import jsonable_encoder
from typing import List, TypeVar
from app.config.mongo import Mongo
from app.util import logging

logger = logging.get_logger("business")

T = TypeVar("T")

async def cursor_to_list(factory: T, cursor) -> List[T]:
    return [factory(**row) async for row in cursor]

__all__ = (
    "Mongo",
    "jsonable_encoder",
    "logger",
    "cursor_to_list",
)
