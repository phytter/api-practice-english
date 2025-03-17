import logging
from app.integration.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


def start_audio_processor() -> None:
    logger.info("Starting audio processor")
    AudioProcessor._startup()

def stop_audio_processor() -> None:
    logger.info("Stopping audio processor")
    AudioProcessor._shutdown()
