from typing import Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, PositiveFloat

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectID")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v

        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectID")
        return ObjectId(v)


__all__ = (
    "BaseModel",
    "Field",
    "PositiveFloat",
    "BooleanField",
    "ObjectId",
    "ObjectIdStr",
    "PyObjectId",
    "List",
    "Dict",
    "Optional",
)
