from typing import List, Any, Optional
from app.core.common.domain.entity import Entity
from app.core.common.domain.value_objects import Uuid

class DialogueLine:
    def __init__(self, character: str, text: str, start_time: float, end_time: float):
        self.character = character
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self._validate_timestamp()
    
    def _validate_timestamp(self) -> None:
        if self.start_time < 0:
            raise ValueError("Start time cannot be negative")
        if self.end_time < self.start_time:
            raise ValueError("End time must be greater than start time")

class DialogueMovie:
    def __init__(self, imdb_id: str, title: str, language: str = "en"):
        self.imdb_id = imdb_id
        self.title = title
        self.language = language

class DialogueEntity(Entity):
    def __init__(
        self, 
        difficulty_level: Optional[int],
        duration_seconds: float,
        lines: List[DialogueLine],
        movie: Optional[DialogueMovie] = None,
        id: Uuid = None
    ):
        self.id = id
        self.movie = movie
        self.difficulty_level = difficulty_level if difficulty_level is not None else self._calculate_difficulty(lines)
        self.duration_seconds = duration_seconds
        self.lines = lines
        self._validate()

    def create(
        duration_seconds: float,
        lines: List[DialogueLine],
        difficulty_level: Optional[int] = None,
        movie: Optional[DialogueMovie] = None,
        id: str = None
    ) -> "DialogueEntity":
        return DialogueEntity(difficulty_level, duration_seconds, lines, movie, Uuid(id))
    
    def _validate(self) -> None:
        self._validate_difficulty_level()
        self._validate_lines()
    
    def _validate_difficulty_level(self) -> None:
        if not 1 <= self.difficulty_level <= 5:
            raise ValueError("Difficulty level must be between 1 and 5")
    
    def _validate_lines(self) -> None:
        if not self.lines:
            raise ValueError("Dialogue must have at least one line")
        
        calculated_duration = self.lines[-1].end_time - self.lines[0].start_time
        if abs(calculated_duration - self.duration_seconds) > 1.0:  # 1 second tolerance
            raise ValueError("Duration doesn't match the dialogue lines timing")
            
    @classmethod
    def _calculate_difficulty(cls, dialogue_lines: List[DialogueLine]) -> int:
        """
        Calculate difficulty level (1-5) based on:
        - Vocabulary complexity
        - Dialogue speed
        - Number of characters
        - Length of dialogues
        """

        if not dialogue_lines:
            return 1
            
        avg_words_per_second = cls._calculate_speech_rate(dialogue_lines)
        vocab_complexity = cls._calculate_vocab_complexity(dialogue_lines)
        num_characters = len(set(line.character for line in dialogue_lines)) or 2
        avg_line_length = sum(len(line.text.split()) for line in dialogue_lines) / len(dialogue_lines)
        
        # Weight and combine factors
        difficulty = (
            (avg_words_per_second * 4) +  # Speed is important
            (vocab_complexity * 3) +      # Vocabulary complexity is important
            (num_characters * 0.5) +      # More characters = slightly harder
            (avg_line_length * 0.6)       # Longer lines = slightly harder
        ) / 5  # Normalize
        
        # Convert to 1-5 scale
        return max(1, min(5, round(difficulty)))
    
    @staticmethod
    def _calculate_speech_rate(lines: List[DialogueLine]) -> float:
        """Calculate average words per second"""
        total_words = 0
        total_duration = 0
        
        for line in lines:
            words = len(line.text.split())
            duration = line.end_time - line.start_time
            total_words += words
            total_duration += duration
        
        return total_words / total_duration if total_duration > 0 else 0

    @staticmethod
    def _calculate_vocab_complexity(lines: List[DialogueLine]) -> float:
        """
        Calculate vocabulary complexity (0-1)
        Based on average word length and presence of complex words
        """
        all_words = []
        for line in lines:
            all_words.extend(line.text.split())
            
        if not all_words:
            return 0
            
        avg_word_length = sum(len(word) for word in all_words) / len(all_words)
        # Normalize to 0-1 range (assuming most words are 2-10 characters)
        return min(1.0, max(0.0, (avg_word_length - 2) / 8))

    def entity_dump(self) -> dict[str, Any]:
        """Convert entity to dictionary for persistence"""
        return {
            "movie": {
                "imdb_id": self.movie.imdb_id,
                "title": self.movie.title,
                "language": self.movie.language
            } if self.movie else None,
            "difficulty_level": self.difficulty_level,
            "duration_seconds": self.duration_seconds,
            "lines": [
                {
                    "character": line.character,
                    "text": line.text,
                    "start_time": line.start_time,
                    "end_time": line.end_time
                } for line in self.lines
            ]
        }