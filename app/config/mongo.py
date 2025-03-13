import logging

from bson import ObjectId

from app.integration import Mongo
from app.util import pydantic

logger = logging.getLogger(__name__)


async def start_mongo() -> None:
    pydantic.register_encoder(ObjectId, str)
    Mongo._startup()


async def stop_mongo() -> None:
    Mongo._shutdown()
