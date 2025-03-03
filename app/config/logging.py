import logging
import sys

from app.util.logging import get_logger


logger = get_logger(__name__)


def start_logging() -> None:
    logging.basicConfig(
        format="{levelname:7}: {message}",
        level=logging.DEBUG,
        handlers=(logging.StreamHandler(sys.stdout),),
        style="{",
    )


async def stop_logging() -> None:
    ...
