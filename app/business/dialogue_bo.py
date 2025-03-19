from typing import List
from datetime import datetime, timezone
import logging
from fastapi import HTTPException, status
from app.model import DialogueOut, ObjectId, PracticeResult, DialoguePracticeHistoryIn, DialoguePracticeHistoryOut, UserOut
from app.integration.mongo import Mongo
from app.integration.audio_processor import AudioProcessor
from app.business.user_bo import UserBusiness
from .base import cursor_to_list

logger = logging.getLogger(__name__)

class DialogueBusiness:
    PAUSE_WORD_THRESHOLD_SECONDS = 0.1
    PRONUNCIATION_THRESHOLD = 0.8
    FLUENCY_THRESHOLD = 0.7

    @classmethod
    async def search_dialogues(
        cls,
        search: str,
        imdb_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[DialogueOut]:
        query = {}
        if search:
            query["$or"] = [
                {"movie.title": {"$regex": search, "$options": "i"}},
                {"lines.text": {"$regex": search, "$options": "i"}},
            ]
        if imdb_id:
            query["movie.imdb_id"] = imdb_id
        cursor = Mongo.dialogues.find(query).skip(skip).limit(limit)
        return await cursor_to_list(DialogueOut, cursor)
    
    @classmethod
    async def get_dialogue (cls, dialogue_id: str) -> DialogueOut:
        if (dialogue :=  await Mongo.dialogues.find_one({"_id": ObjectId(dialogue_id)})) is not None:
            return DialogueOut(**dialogue)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialogue not found"
        )
    
    @classmethod
    async def proccess_practice_dialogue(
        cls,
        dialogue_id: str,
        audio_data: bytes,
        user: UserOut = None
    ) -> PracticeResult:
        dialogue = await cls.get_dialogue(dialogue_id)

        try:
            transcription_result = await AudioProcessor.client.process_audio_transcript(audio_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio processing error: {str(e)}"
            )

        word_scores = [word_score.get('confidence', 0) for word_score in transcription_result.words]
        full_dialogue_text = " ".join(line.text for line in dialogue.lines)

        pronunciation_score = round(sum(word_scores) / len(word_scores), 4) if word_scores else 0.0
        fluency_score = cls._calculate_fluency_score(transcription_result.words)
        suggestions = cls._generate_suggestions(
            pronunciation_score,
            fluency_score,
            transcription_result.transcribed_text,
            full_dialogue_text
        )
        xp_earned = cls._calculate_xp(
            pronunciation_score,
            fluency_score,
            dialogue.difficulty_level
        )

        result = PracticeResult(
            pronunciation_score=pronunciation_score,
            fluency_score=fluency_score,
            transcribed_text=transcription_result.transcribed_text,
            word_timings=transcription_result.words,
            suggestions=suggestions,
            xp_earned=xp_earned
        )

        await cls._create_practice_history(dialogue, user.id, result)
        await UserBusiness.update_progress(user.id, result)

        return result

    @classmethod
    async def list_practice_history(cls, filter_type: str, skip: int = 0, limit: int = 20, user: UserOut = None) -> List[DialoguePracticeHistoryOut]:
        pipeline = [
            {"$match": {"user_id": user.id}},
            {
                "$addFields": {
                    "dialogue_id": {"$toObjectId": "$dialogue_id"}
                }
            },
            {
                "$lookup": {
                    "from": "dialogues",
                    "localField": "dialogue_id",
                    "foreignField": "_id",
                    "as": "dialogue"
                }
            },
            {
                "$addFields": {
                    "dialogue_id": {"$toString": "$dialogue_id"},
                    "dialogue": {"$arrayElemAt": ["$dialogue", 0]}
                }
            },
            {
                "$sort": { "completed_at": -1 } if filter_type == 'recent' else { "xp_earned": -1 }
            },
            {
                "$skip": skip
            },
            {
                "$limit": limit
            }
        ]
        cursor = Mongo.dialogue_practice_history.aggregate(pipeline)
        return await cursor_to_list(DialoguePracticeHistoryOut, cursor)

    @staticmethod
    async def _create_practice_history(dialogue: DialogueOut, user_id: str, result: PracticeResult) -> None:
        try:
            practice_duration = sum(line.end_time - line.start_time for line in dialogue.lines)
            practice_record = DialoguePracticeHistoryIn(
                dialogue_id=dialogue.id,
                user_id=user_id,
                pronunciation_score=result.pronunciation_score,
                fluency_score=result.fluency_score,
                completed_at=datetime.now(timezone.utc),
                practice_duration_seconds=practice_duration,
                character_played='',
                xp_earned=result.xp_earned
            )
            await Mongo.dialogue_practice_history.insert_one(practice_record.model_dump())
        except Exception as e:
            logger.error(f"Error saving practice history: {str(e)}")

    @staticmethod
    def _calculate_fluency_score(word_timings: list) -> float:
        # TODO: Implement more sophisticated fluency scoring
        """
        Calculate fluency score based on word timing and pauses
        """
        if not word_timings:
            return 0.0

        total_pause_time = 0
        total_speaking_time = 0
        previous_end = word_timings[0]["start_time"]

        for timing in word_timings:
            pause_duration = timing["start_time"] - previous_end
            if pause_duration > DialogueBusiness.PAUSE_WORD_THRESHOLD_SECONDS:
                total_pause_time += pause_duration
            total_speaking_time += (timing["end_time"] - timing["start_time"])
            previous_end = timing["end_time"]

        # Calculate fluency score based on pause ratio
        total_time = total_speaking_time + total_pause_time
        if total_time == 0:
            return 0.0

        pause_ratio = total_pause_time / total_time
        # Convert to a score between 0 and 1 (lower pause ratio = higher score)
        fluency_score = max(0, min(1, 1 - pause_ratio))
        return round(fluency_score, 4)

    @staticmethod
    def _generate_suggestions(pronunciation_score: float,
                            fluency_score: float,
                            transcribed_text: str,
                            expected_text: str) -> list:
        """
        Generate improvement suggestions based on scores and text comparison
        """
        suggestions = []

        if pronunciation_score < DialogueBusiness.PRONUNCIATION_THRESHOLD:
            suggestions.append({
                "type": "pronunciation",
                "message": "Try to speak more clearly and enunciate each word"
            })

        if fluency_score < DialogueBusiness.FLUENCY_THRESHOLD:
            suggestions.append({
                "type": "fluency",
                "message": "Try to maintain a more consistent speaking pace with fewer pauses"
            })

        # Simple comparison transcribed_text with expected_text and provide specific suggestions
        transcribed_words = transcribed_text.split()
        expected_words = expected_text.split()
        max_specific_suggestions = 5

        for i, expected_word in enumerate(expected_words):
            if len(suggestions) >= max_specific_suggestions:
                break
            if i < len(transcribed_words):
                transcribed_word = transcribed_words[i]
                if transcribed_word.lower() != expected_word.lower():
                    suggestions.append({
                        "type": "specific",
                        "message": f"Expected '{expected_word}', but you said '{transcribed_word}'."
                    })

        return suggestions
    
    @staticmethod
    def _calculate_xp(pronunciation_score: float, fluency_score: float, difficulty: int) -> int:
        """Calculate XP earned based on performance and difficulty"""
        base_xp = difficulty * 100
        performance_multiplier = (pronunciation_score + fluency_score) / 2
        return int(base_xp * performance_multiplier)