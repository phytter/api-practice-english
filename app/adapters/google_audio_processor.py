from app.core.common.ports import AudioProcessor, AudioTranscriptResult
from google.oauth2 import service_account
from google.cloud import speech_v1

class GoogleAudioProcessor(AudioProcessor):
    min_time_seconds_to_long_running=60
    def __init__(cls):
        credentials = service_account.Credentials.from_service_account_file('google_credentials.json')
        cls.speech_client = speech_v1.SpeechClient(credentials=credentials)
        cls.config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            enable_word_time_offsets=True,
            enable_automatic_punctuation=True,
        )

    async def process_audio_transcript(cls, audio_data: bytes) -> AudioTranscriptResult:

        audio = speech_v1.RecognitionAudio(content=audio_data)

        if cls._get_audio_duration(audio_data) > cls.min_time_seconds_to_long_running:
            operation = cls.speech_client.long_running_recognize(config=cls.config, audio=audio)
            response = operation.result(timeout=90)
        else:
            response = cls.speech_client.recognize(config=cls.config, audio=audio)

        if not response.results:
            return AudioTranscriptResult(
                transcribed_text = '',
                confidence = 0,
                words = []
            )

        transcription = response.results[0].alternatives[0]
        return AudioTranscriptResult(
            transcribed_text = transcription.transcript,
            confidence = transcription.confidence,
            words = [{
                "word": word_info.word,
                "start_time": word_info.start_time.total_seconds(),
                "end_time": word_info.end_time.total_seconds(),
                "confidence": transcription.confidence
            } for word_info in transcription.words]
        )