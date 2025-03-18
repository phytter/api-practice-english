from typing import List
from datetime import datetime, timezone
import logging
from fastapi import HTTPException, status
from app.model import DialogueOut, ObjectId, PracticeResult, DialoguePracticeHistoryIn, DialoguePracticeHistoryOut, UserOut
from app.integration.mongo import Mongo
from app.integration.audio_processor import AudioProcessor

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
        return [DialogueOut(**doc) async for doc in cursor]
    
    @classmethod
    async def show_dialogue (cls, dialogue_id: str) -> DialogueOut:
        dialogue = await Mongo.dialogues.find_one({"_id": ObjectId(dialogue_id)})
        if not dialogue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialogue not found"
            )
        return DialogueOut(**dialogue)
    
    @classmethod
    async def proccess_practice_dialogue(
        cls,
        dialogue_id: str,
        audio_data: bytes,
        user: UserOut = None
    ) -> PracticeResult:
        dialogue = await Mongo.dialogues.find_one({"_id": ObjectId(dialogue_id)})

        if not dialogue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialogue not found"
            )
        
        full_dialogue_text = " ".join(line['text'] for line in dialogue['lines'])
        try:
            transcription_result = await AudioProcessor.client.process_audio_transcript(audio_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Audio processing error: {str(e)}"
            )

        result = {
            "pronunciation_score": 0.0,
            "fluency_score": 0.0,
            "transcribed_text": transcription_result.transcribed_text,
            "word_timings": transcription_result.words,
            "suggestions": []
        }

        word_scores = [word_score.get('confidence', 0) for word_score in transcription_result.words]

        if word_scores:
            result["pronunciation_score"] = round(sum(word_scores) / len(word_scores), 4)
        
        result["fluency_score"] = cls._calculate_fluency_score(transcription_result.words)
        result["suggestions"] = cls._generate_suggestions(
            result["pronunciation_score"],
            result["fluency_score"],
            result["transcribed_text"],
            full_dialogue_text
        )
        xp_earned = cls._calculate_xp(
            result["pronunciation_score"],
            result["fluency_score"],
            dialogue["difficulty_level"]
        )

        result = PracticeResult(
            **result,
            xp_earned=xp_earned
        )

        await cls._create_practice_history(dialogue_id, user.id, result)

        return result

    @classmethod
    async def list_practice_history(cls, skip: int = 0, limit: int = 20, user: UserOut = None) -> List[DialoguePracticeHistoryOut]:
        cursor = Mongo.dialogue_practice_history.find({"user_id": user.id }).skip(skip).limit(limit)
        return [DialoguePracticeHistoryOut(**doc) async for doc in cursor]

    @staticmethod
    async def _create_practice_history(dialogue_id: str, user_id: str, result: PracticeResult) -> None:
        try:
            practice_record = DialoguePracticeHistoryIn(
                dialogue_id=dialogue_id,
                user_id=user_id,
                pronunciation_score=result.pronunciation_score,
                fluency_score=result.fluency_score,
                completed_at=datetime.now(timezone.utc),
                practice_duration=0,
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