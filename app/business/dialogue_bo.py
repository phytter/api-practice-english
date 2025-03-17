from typing import List
from app.model import DialogueOut, ObjectId
from app.integration.mongo import Mongo
from app.integration.audio_processor import AudioProcessor
from fastapi import HTTPException, status

class DialogueBusiness:
    PAUSE_WORD_THRESHOLD = 0.1  # Consider pauses longer than 100ms

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
    async def proccess_practice_dialogue(cls, dialogue_id: str, audio_data: bytes) -> None:
        dialogue = await Mongo.dialogues.find_one({"_id": ObjectId(dialogue_id)})

        if not dialogue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialogue not found"
            )
        
        full_dialogue_text = " ".join(line['text'] for line in dialogue['lines'])
        transcription_result = await AudioProcessor.client.process_audio_transcript(audio_data)

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

        return result

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
            if pause_duration > DialogueBusiness.PAUSE_WORD_THRESHOLD:
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

    def _generate_suggestions(pronunciation_score: float,
                            fluency_score: float,
                            transcribed_text: str,
                            expected_text: str) -> list:
        """
        Generate improvement suggestions based on scores and text comparison
        """
        suggestions = []

        if pronunciation_score < 0.8:
            suggestions.append({
                "type": "pronunciation",
                "message": "Try to speak more clearly and enunciate each word"
            })

        if fluency_score < 0.7:
            suggestions.append({
                "type": "fluency",
                "message": "Try to maintain a more consistent speaking pace with fewer pauses"
            })

        # Simple comparison transcribed_text with expected_text and provide specific suggestions
        transcribed_words = transcribed_text.split()
        expected_words = expected_text.split()

        for i, expected_word in enumerate(expected_words):
            if i < len(transcribed_words):
                transcribed_word = transcribed_words[i]
                if transcribed_word.lower() != expected_word.lower():
                    suggestions.append({
                        "type": "specific",
                        "message": f"Expected '{expected_word}', but you said '{transcribed_word}'."
                    })

        return suggestions