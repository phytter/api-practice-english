from .value_object import ValueObject
from typing import Optional, Union
from bson import ObjectId as BsonObjectId

class Uuid(ValueObject):
    def __init__(self, value: Optional[Union[str, BsonObjectId]] = None):
        self._value = BsonObjectId() if value is None else value
        if isinstance(self._value, str):
            self._value = BsonObjectId(self._value)
        self._validate()
    
    def _validate(self):
        if not isinstance(self._value, BsonObjectId):
            if isinstance(self._value, str):
                if not BsonObjectId.is_valid(self._value):
                    raise ValueError(f"Invalid BsonObjectId: {self._value}")
                self._value = BsonObjectId(self._value)
            else:
                raise ValueError(f"Value must be BsonObjectId or valid string, got {type(self._value)}")
    
    def __eq__(cls, other: object) -> bool:
        if not isinstance(other, Uuid):
            return False
        return cls._value == other._value
    
    def __str__(cls) -> str:
      return str(cls._value)
