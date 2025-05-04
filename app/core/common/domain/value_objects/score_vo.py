from app.core.common.domain.value_objects.value_object import ValueObject

class Score(ValueObject):
    def __init__(cls, value: float):
        cls._value = value
        cls._validate()
    
    def _validate(cls):
        if not 0 <= cls._value <= 1:
            raise ValueError(f"Score must be between 0 and 1, got {cls._value}")
    
    def __eq__(cls, other: object) -> bool:
        if not isinstance(other, Score):
            return False
        return cls._value == other._value
    
    def __float__(cls) -> float:
        return cls._value

    def __str__(cls) -> str:
        return str(cls._value)