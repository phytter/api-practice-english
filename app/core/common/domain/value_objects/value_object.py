# app/core/common/domain/value_object.py
from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar('T', bound='ValueObject')

class ValueObject(ABC):
    
    @property
    def value(cls) -> str:
        return cls._value
    
    @abstractmethod
    def _validate(cls) -> bool:
        """Value objects must implement validation"""
        pass
    
    @abstractmethod
    def __eq__(cls, other: object) -> bool:
        """Value objects must implement equality comparison"""
        pass
    
