import re
from typing import List, Tuple
from app.core.dialogues.domain.dialogue_entity import DialogueEntity, DialogueLine, DialogueMovie

class SubtitlesBussiness:

    @classmethod
    def process_subtitle_content(cls, content: str, movie: DialogueMovie = None) -> List[DialogueEntity]:
        """Process subtitle content into structured dialogues"""

        dialogue_lines = cls._extract_dialogues(content)
        scenes = cls._group_into_scenes(dialogue_lines)

        return [DialogueEntity.create(
            lines=scene,
            duration_seconds=scene[-1].end_time - scene[0].start_time,
            movie=movie
        ) for scene in scenes]

    @classmethod
    def _extract_dialogues(cls, subtitle_content: str) -> List[DialogueLine]:
        """Extract dialogues from subtitle content with character identification"""
        dialogue_lines = []
        min_length_to_be_valid_block = 3
        
        subtitle_blocks = re.split(r'\n\n+', subtitle_content.strip())
        
        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) < min_length_to_be_valid_block:
                continue
                
            timestamp = lines[1]
            start_time, end_time = cls._parse_timestamp(timestamp)
            
            # Parse text and identify character
            text = '\n'.join(lines[2:])
            dialogues = cls._identify_all_characters(text)
            
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
        
        return cls._merge_consecutive_lines(dialogue_lines)

    @classmethod
    def _clear_text_dialogue(cls, text: str) -> str:
        return cls._remove_dots(cls._remove_html_tags(text))

    @classmethod
    def _identify_all_characters(cls, text: str) -> List[Tuple[str, str]]:
        dialogues = []
        lines = text.splitlines()
        
        for line in lines:
            character, dialogue = cls._identify_character(line)
            
            if character and dialogue:
                dialogues.append((character, dialogue))
            elif dialogues and character == "":
                last_character, last_dialogue = dialogues[-1]
                dialogues.append((last_character, dialogue))
            else:
                dialogues.append(("", dialogue))
        return dialogues

    @classmethod
    def _identify_character(cls, text: str) -> Tuple[str, str]:
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
                return character, cls._clear_text_dialogue(dialogue)
        
        return "", cls._clear_text_dialogue(text.strip())

    @staticmethod
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

    @staticmethod
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
                current_line.text += " " + next_line.text
                current_line.end_time = next_line.end_time
            else:
                merged_lines.append(current_line)
                current_line = next_line
        
        merged_lines.append(current_line)
        return merged_lines

    @staticmethod
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

    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """Remove HTML tags from the given text."""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    @staticmethod
    def _remove_dots(text: str) -> str:
        """Remove all dots from the given text."""
        return text.replace('.', '').replace('-', '')

