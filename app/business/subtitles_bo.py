import re
from typing import List, Tuple
from app.model import Dialogue, DialogueLine

class SubtitlesBussiness:

    @classmethod
    def process_subtitle_content(self, content: str) -> List[Dialogue]:
        """Process subtitle content into structured dialogues"""

        dialogue_lines = self.extract_dialogues(content)
        difficulty_level = self.calculate_difficulty(dialogue_lines)
        scenes = self._group_into_scenes(dialogue_lines)

        return [Dialogue(
            lines = [dict(line) for line in scene],
            duration_seconds = scene[-1].end_time - scene[0].start_time,
            difficulty_level = difficulty_level,
            characters = list(set(line.character for line in scene))
        ) for scene in scenes]

    def _group_into_scenes(lines: List[DialogueLine], 
                          max_gap: float = 5.0,
                          min_lines: int = 5,
                          max_duration: float = 180) -> List[List[DialogueLine]]:
        """
        Group dialogue lines into scenes based on time gaps and constraints
        - max_gap: maximum time gap between lines to be considered same scene
        - min_lines: minimum number of lines for a valid scene
        - max_duration: maximum duration of a scene in seconds
        """
        if not lines:
            return []

        scenes = []
        current_scene = [lines[0]]
        
        for line in lines[1:]:
            time_gap = line.start_time - current_scene[-1].end_time
            scene_duration = line.end_time - current_scene[0].start_time
            
            if (time_gap <= max_gap and scene_duration <= max_duration):
                current_scene.append(line)
            else:
                if len(current_scene) >= min_lines:
                    scenes.append(current_scene)
                current_scene = [line]
        
        if len(current_scene) >= min_lines:
            scenes.append(current_scene)
        
        return scenes

    @classmethod
    def extract_dialogues(self, subtitle_content: str) -> List[DialogueLine]:
        """Extract dialogues from subtitle content with character identification"""
        dialogue_lines = []
        min_length_to_be_valid_block = 3
        
        subtitle_blocks = re.split(r'\n\n+', subtitle_content.strip())
        
        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) < min_length_to_be_valid_block:
                continue
                
            timestamp = lines[1]
            start_time, end_time = self._parse_timestamp(timestamp)
            
            # Parse text and identify character
            text = '\n'.join(lines[2:])
            dialogues = self._identify_all_characters(text)
            
            for character, dialogue in dialogues:
                if dialogue:
                    dialogue_lines.append(
                        DialogueLine(
                            character=character,
                            text=dialogue,
                            start_time=start_time,
                            end_time=end_time
                        )
                    )
        
        return self._merge_consecutive_lines(dialogue_lines)

    def _parse_timestamp(timestamp: str) -> Tuple[float, float]:
        """Convert SRT timestamp to seconds"""
        pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})'
        match = re.match(pattern, timestamp)
        if not match:
            return 0.0, 0.0
            
        groups = match.groups()
        start_time = (
            int(groups[0]) * 3600 +  # hours
            int(groups[1]) * 60 +    # minutes
            int(groups[2]) +         # seconds
            int(groups[3]) / 1000    # milliseconds
        )
        
        end_time = (
            int(groups[4]) * 3600 +
            int(groups[5]) * 60 +
            int(groups[6]) +
            int(groups[7]) / 1000
        )
        
        return start_time, end_time

    def _remove_html_tags(text: str) -> str:
        """Remove HTML tags from the given text."""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)


    def _remove_dots(text: str) -> str:
        """Remove all dots from the given text."""
        return text.replace('.', '').replace('-', '')
    
    @classmethod
    def _clear_text_dialogue (self, text: str) -> str:
        return self._remove_dots(self._remove_html_tags(text))

    @classmethod
    def _identify_all_characters(self, text: str) -> List[Tuple[str, str]]:
        dialogues = []
        lines = text.splitlines()
        
        for line in lines:
            character, dialogue = self._identify_character(line)
            
            if character and dialogue:
                dialogues.append((character, dialogue))
            elif dialogues and character == "":
                last_character, last_dialogue = dialogues[-1]
                dialogues.append((last_character, dialogue))
            else:
                dialogues.append(("", dialogue))
        return dialogues

    @classmethod
    def _identify_character(self, text: str) -> Tuple[str, str]:
        """
        Identify character name and dialogue from text
        Returns tuple of (character_name, dialogue_text)
        """
        # Common patterns for character identification
        patterns = [
            r'^([A-Z][A-Z\s]+):\s*(.*)',  # JOHN: Hello there
            r'^([A-Z][a-z]+):\s*(.*)',    # John: Hello there
            r'\[([^\]]+)\]\s*(.*)',       # [JOHN] Hello there
            r'\(([^\)]+)\)\s*(.*)',       # (JOHN) Hello there
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text.strip())
            if match:
                character = match.group(1).strip()
                dialogue = match.group(2).strip()
                return character, self._clear_text_dialogue(dialogue)
        
        return "", self._clear_text_dialogue(text.strip())

    def _merge_consecutive_lines(lines: List[DialogueLine]) -> List[DialogueLine]:
        """Merge consecutive lines from the same character"""
        if not lines:
            return lines
            
        merged_lines = []
        current_line = lines[0]
        
        for next_line in lines[1:]:
            # If same character and small time gap (less than 2 seconds)
            if (current_line.character and current_line.character == next_line.character and
                next_line.start_time - current_line.end_time < 2.0):
                # Merge lines
                current_line.text += " " + next_line.text
                current_line.end_time = next_line.end_time
            else:
                merged_lines.append(current_line)
                current_line = next_line
        
        merged_lines.append(current_line)
        return merged_lines

    @classmethod
    def calculate_difficulty(self, dialogue_lines: List[DialogueLine]) -> int:
        """
        Calculate difficulty level (1-5) based on:
        - Vocabulary complexity
        - Dialogue speed
        - Number of characters
        - Length of dialogues
        """

        if not dialogue_lines:
            return 1
            
        avg_words_per_second = self._calculate_speech_rate(dialogue_lines)
        vocab_complexity = self._calculate_vocab_complexity(dialogue_lines)
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
