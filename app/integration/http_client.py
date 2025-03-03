import logging
from typing import Optional

from aiohttp import ClientSession


logger = logging.getLogger(__name__)


class HttpClient:
    session: Optional[ClientSession] = None

    @classmethod
    async def startup(cls) -> None:
        if cls.session:
            logger.warning("HttpClient already exists!")
            return

        logger.info("Starting HttpClient...")
        cls.session = ClientSession()

    @classmethod
    async def shutdown(cls) -> None:
        if not (session := cls.session):
            logger.warning("HttpClient alredy stopped!")
            return

        logger.info("Stopping HttpClient...")
        cls.session = None
        await session.close()
