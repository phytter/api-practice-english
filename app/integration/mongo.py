import logging
from typing import Optional

from motor.core import AgnosticClient, AgnosticCollection, AgnosticDatabase
from motor.motor_asyncio import AsyncIOMotorClient

from ..core.config import settings


logger = logging.getLogger(__name__)


class Mongo:

    client: Optional[AgnosticClient] = None
    db: Optional[AgnosticDatabase] = None

    users: AgnosticCollection = None

    @classmethod
    async def ping(cls) -> None:
        await cls.client.admin.command({"ping": 1})

    @classmethod
    async def get_version(cls):
        v = await cls.db.command({"serverStatus": 1})
        return f"Using MongoDB v.{v['version']}"

    @classmethod
    def _startup(cls) -> None:
        if cls.client is not None:
            raise RuntimeError("Database has already been started")

        logger.info("Starting MongoDB database: %s", settings.MONGODB_URL)

        cls.client = AsyncIOMotorClient(settings.MONGODB_URL, tz_aware=True)
        cls.db = cls.client.get_default_database(settings.DATABASE_NAME)

    @classmethod
    def _shutdown(cls) -> None:
        if cls.client is None:
            raise RuntimeError("Database has already been shut down")

        cls.client.close()
