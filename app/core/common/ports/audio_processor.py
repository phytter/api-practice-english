from abc import ABC, abstractmethod
from pydub import AudioSegment
import io
from pydantic import BaseModel
from typing import Dict

class AudioTranscriptResult(BaseModel):
    transcribed_text: str
    words: list[Dict]
    confidence: float

class AudioProcessor(ABC):

    @abstractmethod
    async def process_audio_transcript(cls, audio_data: bytes) -> AudioTranscriptResult:
        pass

    def _get_audio_duration(self, audio_data: bytes) -> float:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        duration = len(audio_segment) / 1000.0  # Convert to seconds
        return duration