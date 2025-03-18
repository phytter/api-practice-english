import pytest
import pytest_asyncio
from unittest.mock import patch
from httpx import AsyncClient
from app.http.rest.v1 import dialogue_v1
from app.integration.mongo import Mongo
from app.model import ObjectId
import io
from google.cloud import speech_v1
from pydub import AudioSegment

BASE_URL = dialogue_v1.prefix
MOVIE_IMDB_ID = "123"
pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("wipe_data")]

@pytest_asyncio.fixture
async def wipe_data():
    await Mongo.dialogues.delete_many({})
    await Mongo.dialogue_practice_history.delete_many({})

def mock_dialogue():
    return {
      "movie": {
          "imdb_id": MOVIE_IMDB_ID,
          "title": "The Movie",
          "language": "en"
      },
      "difficulty_level": 2,
      "lines": [{ "character": "", "text": "", "start_time": 10, "end_time": 20 }],
      "duration_seconds": 10
    }

def mock_audio():
    silent_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
    audio_file = io.BytesIO()
    silent_audio.export(audio_file, format="webm")
    audio_file.name = "audio.webm"
    audio_file.seek(0)
    return audio_file

def mock_practice_history_db(dialogue_id: str | ObjectId):
    return {
        "dialogue_id": str(dialogue_id),
        "user_id": "user_id",
        "pronunciation_score": 0.8,
        "fluency_score": 1,
        "completed_at": "2021-01-01T00:00:00",
        "practice_duration_seconds": 10,
        "character_played": "",
        "xp_earned": 10
    }

def mock_google_speech_good_result(transcript=""):
    return speech_v1.RecognizeResponse(
        results = [
            speech_v1.SpeechRecognitionResult(
                alternatives = [speech_v1.SpeechRecognitionAlternative(
                    confidence = 0.8,
                    transcript = transcript or "buzz lightyear mission log",
                    words = [
                        speech_v1.WordInfo(
                            word = "Buzz",
                            start_time = {"seconds": 0, "nanos": 0},
                            end_time = {"seconds": 0, "nanos": 500000000},
                        ),
                        speech_v1.WordInfo(
                            word = "lightyear",
                            start_time = {"seconds": 0, "nanos": 500000000},
                            end_time = {"seconds": 1, "nanos": 0},
                        ),
                        speech_v1.WordInfo(
                            word = "mission",
                            start_time = {"seconds": 1, "nanos": 0},
                            end_time = {"seconds": 1, "nanos": 500000000},
                        ),
                        speech_v1.WordInfo(
                            word = "log",
                            start_time = {"seconds": 1, "nanos": 500000000},
                            end_time = {"seconds": 2, "nanos": 0},
                        )
                    ]
                )]
            )
        ]
    )

def mock_google_speech_bad_result(transcript=""):
    return speech_v1.RecognizeResponse(
        results = [
            speech_v1.SpeechRecognitionResult(
                alternatives = [speech_v1.SpeechRecognitionAlternative(
                    confidence = 0.58,
                    transcript = transcript or "buzz lightyear mission log as the location of zurg's fortress",
                    words = [
                        speech_v1.WordInfo(
                            word = "Buzz",
                            start_time = {"seconds": 0, "nanos": 0},
                            end_time = {"seconds": 0, "nanos": 500000000},
                        ),
                        speech_v1.WordInfo(
                            word = "lightyear",
                            start_time = {"seconds": 2, "nanos": 500000000},
                            end_time = {"seconds": 2, "nanos": 0},
                        ),
                        speech_v1.WordInfo(
                            word = "mission",
                            start_time = {"seconds": 2, "nanos": 500000000},
                            end_time = {"seconds": 3, "nanos": 500000000},
                        ),
                        speech_v1.WordInfo(
                            word = "log",
                            start_time = {"seconds": 4, "nanos": 500000000},
                            end_time = {"seconds": 4, "nanos": 0},
                        ),
                        speech_v1.WordInfo(
                            word = "as",
                            start_time = {"seconds": 5, "nanos": 0},
                            end_time = {"seconds": 5, "nanos": 500000000},
                        ),
                        speech_v1.WordInfo(
                            word = "the",
                            start_time = {"seconds": 6, "nanos": 500000000},
                            end_time = {"seconds": 6, "nanos": 0},
                        ),
                        speech_v1.WordInfo(
                            word = "location",
                            start_time = {"seconds": 8, "nanos": 0},
                            end_time = {"seconds": 9, "nanos": 500000000},
                        ),
                        speech_v1.WordInfo(
                            word = "of",
                            start_time = {"seconds": 9, "nanos": 500000000},
                            end_time = {"seconds": 9, "nanos": 0},
                        ),
                        speech_v1.WordInfo(
                            word = "zurg",
                            start_time = {"seconds": 11, "nanos": 0},
                            end_time = {"seconds": 12, "nanos": 500000000},
                        ),
                        speech_v1.WordInfo(
                            word = "fortress",
                            start_time = {"seconds": 12, "nanos": 500000000},
                            end_time = {"seconds": 13, "nanos": 0},
                        )
                    ]
                )]
            )
        ]
    )
  
async def test_search_dialogues_empty_results(client: AsyncClient):

    res = await client.get(BASE_URL)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

async def test_search_dialogues(client: AsyncClient):

    dialogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dialogue_db)

    res = await client.get(BASE_URL)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['title'] == dialogue_db['movie']['title']

async def test_search_dialogues_with_query(client: AsyncClient):

    dialogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dialogue_db)

    res = await client.get(f"{BASE_URL}?search=not_included")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

    res = await client.get(f"{BASE_URL}?search={dialogue_db['movie']['title']}")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['title'] == dialogue_db['movie']['title']

async def test_search_dialogues_with_imdb(client: AsyncClient):

    dialogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dialogue_db)

    res = await client.get(f"{BASE_URL}?imdb_id=not_included")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

    res = await client.get(f"{BASE_URL}?imdb_id={MOVIE_IMDB_ID}")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['imdb_id'] == MOVIE_IMDB_ID


async def test_search_dialogues_with_pagination(client: AsyncClient):

    await Mongo.dialogues.insert_one(mock_dialogue())
    await Mongo.dialogues.insert_one(mock_dialogue())

    res = await client.get(f"{BASE_URL}?limit=1&skip=0")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1

    res = await client.get(f"{BASE_URL}?limit=2&skip=0")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 2


    res = await client.get(f"{BASE_URL}?limit=2&skip=1")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1


    res = await client.get(f"{BASE_URL}?limit=2&skip=2")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

async def test_get_dialogue(client: AsyncClient):

    dialogue_db = mock_dialogue()
    result = await Mongo.dialogues.insert_one(dialogue_db)
    dialogue_id = result.inserted_id

    res = await client.get(f"{BASE_URL}/{dialogue_id}")

    json_data = res.json()

    assert res.status_code == 200
    assert json_data['movie']['imdb_id'] == MOVIE_IMDB_ID
    assert json_data['_id'] == str(dialogue_id)

    non_existent_id = ObjectId()
    res = await client.get(f"{BASE_URL}/{non_existent_id}")

    json_data = res.json()

    assert res.status_code == 404
    assert json_data['detail'] == "Dialogue not found"

async def test_practice_dialogue_not_found_error(client: AsyncClient):
    audio_file = mock_audio()
    non_existent_id = ObjectId()
    res = await client.post(f"{BASE_URL}/{non_existent_id}/practice", files={"audio": (audio_file.name, audio_file, "audio/webm")})

    assert res.status_code == 404

@patch("google.cloud.speech_v1.SpeechClient.recognize")
async def test_practice_dialogue_positive_return(mock_audio_transcript, client: AsyncClient):
    mock_audio_transcript.return_value = mock_google_speech_good_result()
    dialogue_db = mock_dialogue()
    dialogue_db['lines'] = [
        { "character": "", "text": "Buzz lightyear mission log", "start_time": 0, "end_time": 2 },
    ]
    result = await Mongo.dialogues.insert_one(dialogue_db)
    dialogue_id = result.inserted_id

    audio_file = mock_audio()
    res = await client.post(f"{BASE_URL}/{dialogue_id}/practice", files={"audio": (audio_file.name, audio_file, "audio/webm")})
    result_json = res.json()

    assert res.status_code == 200
    assert result_json['pronunciation_score'] == 0.8
    assert result_json['fluency_score'] == 1
    assert result_json['transcribed_text'] == "buzz lightyear mission log"
    assert len(result_json['suggestions']) == 0
    assert len(result_json['word_timings']) == 4

@patch("google.cloud.speech_v1.SpeechClient.recognize")
async def test_practice_dialogue_suggestions_return(mock_audio_transcript, client: AsyncClient):
    transcribed_text = "bus light mission lag as the location of zurg's fort"
    mock_audio_transcript.return_value = mock_google_speech_bad_result(transcribed_text)
    dialogue_db = mock_dialogue()
    dialogue_db['lines'] = [
        { "character": "", "text": "Buzz lightyear mission log", "start_time": 0, "end_time": 2 },
        { "character": "", "text": "as the location of zurg's fortress", "start_time": 2, "end_time": 4 },
    ]
    result = await Mongo.dialogues.insert_one(dialogue_db)
    dialogue_id = result.inserted_id

    audio_file = mock_audio()
    res = await client.post(f"{BASE_URL}/{dialogue_id}/practice", files={"audio": (audio_file.name, audio_file, "audio/webm")})
    result_json = res.json()

    assert res.status_code == 200
    assert result_json['pronunciation_score'] == 0.58
    assert result_json['fluency_score'] == 0.2692
    assert result_json['transcribed_text'] == transcribed_text
    assert len(result_json['suggestions']) == 5
    assert len(result_json['word_timings']) == 10

async def test_list_practice_history(client: AsyncClient, mock_auth_user_and_header):
    user_auth, headers = mock_auth_user_and_header

    dialogue_db = mock_dialogue()
    result = await Mongo.dialogues.insert_one(dialogue_db)
    dialogue_id = result.inserted_id

    practice_history = mock_practice_history_db(dialogue_id)
    practice_history['user_id'] = user_auth['_id']
    await Mongo.dialogue_practice_history.insert_one(practice_history)

    res = await client.get(f"{BASE_URL}/practice/history", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['dialogue_id'] == practice_history['dialogue_id']
    assert json_data[0]['user_id'] == practice_history['user_id']
    assert json_data[0]['pronunciation_score'] == practice_history['pronunciation_score']
    assert json_data[0]['fluency_score'] == practice_history['fluency_score']
    assert json_data[0]['completed_at'] == practice_history['completed_at']
    assert json_data[0]['practice_duration_seconds'] == practice_history['practice_duration_seconds']
    assert json_data[0]['character_played'] == practice_history['character_played']
    assert json_data[0]['xp_earned'] == practice_history['xp_earned']

    practice_history = mock_practice_history_db(dialogue_id)
    practice_history['user_id'] = user_auth['_id']
    await Mongo.dialogue_practice_history.insert_one(practice_history)

    res = await client.get(f"{BASE_URL}/practice/history?limit=1&skip=0", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1

    res = await client.get(f"{BASE_URL}/practice/history?limit=2&skip=0", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 2

    res = await client.get(f"{BASE_URL}/practice/history?limit=2&skip=1", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1

    res = await client.get(f"{BASE_URL}/practice/history?limit=2&skip=2", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0