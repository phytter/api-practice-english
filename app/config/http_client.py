import logging

from app.integration.http_client import HttpClient


logger = logging.getLogger(__name__)


async def start_http_client() -> None:
    await HttpClient.startup()

async def stop_http_client() -> None:
    await HttpClient.shutdown()
