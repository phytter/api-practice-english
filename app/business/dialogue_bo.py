import difflib
import re
from typing import List
from datetime import datetime, timezone
import logging
from fastapi import HTTPException, status
from app.core.dialogues.application.dto.dialogue_dto import DialogueOut, PracticeResult, DialoguePracticeHistoryOut
from app.core.users.application.dto.user_dto import UserOut
from app.integration.audio_processor import AudioProcessor
from app.business.user_bo import UserBusiness
from app.core.dialogues.infra.database.repositories import DialogueMongoRepository, DialoguePracticeHistoryMongoRepository
from app.core.dialogues.application import DialogueMapper, DialoguePracticeHistoryMapper
from app.core.dialogues.domain import DialoguePracticeHistoryEntity

logger = logging.getLogger(__name__)

class DialogueBusiness:
    PAUSE_WORD_THRESHOLD_SECONDS = 0.1
    PRONUNCIATION_THRESHOLD = 0.8
    FLUENCY_THRESHOLD = 0.7
    WORD_ACCURACY_THRESHOLD = 0.6
    dialogue_repo = DialogueMongoRepository()
    dialogue_practice_history_repo = DialoguePracticeHistoryMongoRepository()

    @classmethod
    async def search_dialogues(
        cls,
        search: str,
        imdb_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[DialogueOut]:

        entities = await cls.dialogue_repo.find_with_filters({ "imdb_id": imdb_id, "search": search }, skip, limit)    
        return [DialogueMapper.to_dto(entity) for entity in entities]
    
    @classmethod
    async def get_dialogue (cls, dialogue_id: str) -> DialogueOut:
        entity = await cls.dialogue_repo.find_by_id(dialogue_id)
        
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialogue not found"
            )
        
        return DialogueMapper.to_dto(entity)
    
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

        avg_confidence = round(sum(word_scores) / len(word_scores), 4) if word_scores else 0.0
        word_accuracy = cls._calculate_word_accuracy(transcription_result.transcribed_text, full_dialogue_text)
        pronunciation_score = round(0.6 * word_accuracy + 0.4 * avg_confidence, 4)

        expected_word_count = len(cls._normalize_words(full_dialogue_text))
        fluency_score = cls._calculate_fluency_score(
            transcription_result.words,
            dialogue.duration_seconds,
            expected_word_count,
        )
        suggestions = cls._generate_suggestions(
            pronunciation_score,
            fluency_score,
            word_accuracy,
            transcription_result.transcribed_text,
            full_dialogue_text,
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
        
        # Publish dialogue-related domain events only
        await cls._publish_practice_events(dialogue, user.id, result)

        return result

    @classmethod
    async def list_practice_history(cls, filter_type: str, skip: int = 0, limit: int = 20, user: UserOut = None) -> List[DialoguePracticeHistoryOut]:
        filters = {
            "user_id": user.id,
            "sort_field": "completed_at" if filter_type == 'recent' else "xp_earned",
            "sort_desc": True
        }
        
        entities = await cls.dialogue_practice_history_repo.find_with_filters(
            filters, 
            skip, 
            limit,
            include_dialogue=True
        )
        
        return [DialoguePracticeHistoryMapper.to_dto(entity, include_dialogue=True) for entity in entities]

    @classmethod
    async def _create_practice_history(cls, dialogue: DialogueOut, user_id: str, result: PracticeResult) -> None:
        try:
            practice_duration = sum(line.end_time - line.start_time for line in dialogue.lines)
            practice_entity = DialoguePracticeHistoryEntity.create(
                dialogue_id=dialogue.id,
                user_id=user_id,
                pronunciation_score=result.pronunciation_score,
                fluency_score=result.fluency_score,
                completed_at=datetime.now(timezone.utc),
                practice_duration_seconds=practice_duration,
                character_played='',
                xp_earned=result.xp_earned
            )

            await cls.dialogue_practice_history_repo.create(practice_entity)
        except Exception as e:
            logger.error(f"Error saving practice history: {str(e)}")

    @staticmethod
    def _calculate_fluency_score(word_timings: list, expected_duration: float, expected_word_count: int) -> float:
        if not word_timings:
            return 0.0

        total_pause_time = 0.0
        total_speaking_time = 0.0
        previous_end = word_timings[0]["start_time"]

        for timing in word_timings:
            pause_duration = timing["start_time"] - previous_end
            if pause_duration > DialogueBusiness.PAUSE_WORD_THRESHOLD_SECONDS:
                total_pause_time += pause_duration
            total_speaking_time += timing["end_time"] - timing["start_time"]
            previous_end = timing["end_time"]

        total_time = total_speaking_time + total_pause_time
        if total_time == 0:
            return 0.0

        pause_score = max(0.0, min(1.0, 1.0 - total_pause_time / total_time))

        rate_score = 1.0
        actual_duration = word_timings[-1]["end_time"] - word_timings[0]["start_time"]
        if expected_duration > 0 and expected_word_count > 0 and actual_duration > 0:
            expected_wps = expected_word_count / expected_duration
            actual_wps = len(word_timings) / actual_duration
            rate_deviation = abs(actual_wps - expected_wps) / expected_wps
            rate_score = max(0.0, min(1.0, 1.0 - rate_deviation))

        return round(0.7 * pause_score + 0.3 * rate_score, 4)

    @staticmethod
    def _generate_suggestions(
        pronunciation_score: float,
        fluency_score: float,
        word_accuracy: float,
        transcribed_text: str,
        expected_text: str,
    ) -> list:
        suggestions = []

        if word_accuracy < DialogueBusiness.WORD_ACCURACY_THRESHOLD:
            suggestions.append({
                "type": "accuracy",
                "message": "Focus on saying the correct words — try reading the dialogue aloud before recording",
            })
        elif pronunciation_score < DialogueBusiness.PRONUNCIATION_THRESHOLD:
            suggestions.append({
                "type": "pronunciation",
                "message": "Try to speak more clearly and enunciate each word",
            })

        if fluency_score < DialogueBusiness.FLUENCY_THRESHOLD:
            suggestions.append({
                "type": "fluency",
                "message": "Try to maintain a more consistent speaking pace with fewer pauses",
            })

        transcribed_words = DialogueBusiness._normalize_words(transcribed_text)
        expected_words = DialogueBusiness._normalize_words(expected_text)

        if not expected_words:
            return suggestions

        matcher = difflib.SequenceMatcher(None, expected_words, transcribed_words)
        specific_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if specific_count >= 5:
                break
            if tag == 'replace':
                exp_slice = expected_words[i1:i2]
                got_slice = transcribed_words[j1:j2]
                for k, exp_word in enumerate(exp_slice):
                    if specific_count >= 5:
                        break
                    got_word = got_slice[k] if k < len(got_slice) else '[inaudible]'
                    suggestions.append({
                        "type": "specific",
                        "message": f"You said '{got_word}' — the correct word is '{exp_word}'",
                    })
                    specific_count += 1
            elif tag == 'delete':
                for word in expected_words[i1:i2]:
                    if specific_count >= 5:
                        break
                    suggestions.append({
                        "type": "specific",
                        "message": f"You missed the word '{word}'",
                    })
                    specific_count += 1

        return suggestions
    
    @staticmethod
    def _calculate_xp(pronunciation_score: float, fluency_score: float, difficulty: int) -> int:
        """Calculate XP earned based on performance and difficulty"""
        base_xp = difficulty * 100
        performance_multiplier = (pronunciation_score + fluency_score) / 2
        return int(base_xp * performance_multiplier)

    @staticmethod
    def _normalize_words(text: str) -> list:
        cleaned = re.sub(r"[^\w\s']", '', text.lower())
        return [w.strip("'") for w in cleaned.split() if w.strip("'")]

    @staticmethod
    def _calculate_word_accuracy(transcribed_text: str, expected_text: str) -> float:
        transcribed_words = DialogueBusiness._normalize_words(transcribed_text)
        expected_words = DialogueBusiness._normalize_words(expected_text)
        if not expected_words:
            return 0.0
        matcher = difflib.SequenceMatcher(None, expected_words, transcribed_words)
        matches = sum(block.size for block in matcher.get_matching_blocks())
        return round(min(1.0, matches / len(expected_words)), 4)

    @classmethod
    async def _publish_practice_events(
        cls,
        dialogue: DialogueOut,
        user_id: str,
        result: PracticeResult
    ) -> None:
        """Publish dialogue-related domain events"""
        from app.core.common.domain.events.event_dispatcher import event_dispatcher
        from app.core.dialogues.domain.events.practice_completed_event import PracticeCompletedEvent
        from app.core.common.domain.value_objects import Uuid, Score, XpPoints
        
        try:
            # Create and publish practice completed event
            practice_duration = sum(line.end_time - line.start_time for line in dialogue.lines)
            practice_event = PracticeCompletedEvent(
                user_id=Uuid(user_id),
                dialogue_id=Uuid(dialogue.id),
                pronunciation_score=Score(result.pronunciation_score),
                fluency_score=Score(result.fluency_score),
                xp_earned=XpPoints(result.xp_earned),
                practice_duration_seconds=practice_duration,
                difficulty_level=dialogue.difficulty_level,
                character_played=""
            )
            
            await event_dispatcher.publish(practice_event)
            
        except Exception as e:
            logger.error(f"Error publishing practice domain events: {str(e)}")