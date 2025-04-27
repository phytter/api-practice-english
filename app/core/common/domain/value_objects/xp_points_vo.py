from app.core.common.domain.value_objects.value_object import ValueObject

class XpPoints(ValueObject):
    def __init__(cls, value: int):
        cls._value = value
        cls._validate()
    
    def _validate(cls):
        if cls._value < 0:
            raise ValueError(f"XP points cannot be negative, got {cls._value}")
    
    def __eq__(cls, other: object) -> bool:
        if not isinstance(other, XpPoints):
            return False
        return cls._value == other._value
    
    def add(cls, points: int) -> 'XpPoints':
        """Creates a new XpPoints with added value"""
        return XpPoints(cls._value + points)
    
    def __str__(cls) -> str:
        return str(cls._value)