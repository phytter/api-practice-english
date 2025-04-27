import re
from typing import ClassVar
from app.core.common.domain.value_objects.value_object import ValueObject

class Email(ValueObject):
    EMAIL_PATTERN: ClassVar[str] = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    
    def __init__(cls, value: str):
        cls._value = value
        cls._validate()
    
    def _validate(cls):
        if not cls._value:
            raise ValueError("Email cannot be empty")
        
        if not re.match(cls.EMAIL_PATTERN, cls._value):
            raise ValueError(f"Invalid email format: {cls._value}")
    
    def __eq__(cls, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return cls._value.lower() == other._value.lower()
    
    def __str__(cls) -> str:
        return cls._value
