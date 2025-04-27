from app.adapters.google_audio_processor import GoogleAudioProcessor
from app.core.common.ports import AudioProcessor as AudioProcessorPort

class AudioProcessor:
    client: AudioProcessorPort = None

    @classmethod
    def _startup(cls) -> None:
      if cls.client is not None:
          raise RuntimeError("Audio processor has already been started")

      cls.client = GoogleAudioProcessor()

    @classmethod
    def _shutdown(cls) -> None:
       pass