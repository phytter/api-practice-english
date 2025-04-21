from typing import Dict, List, Optional, Any

from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, GetCoreSchemaHandler

from pydantic_core import core_schema

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        def validate(value: Any, info: core_schema.ValidationInfo) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str):
                if ObjectId.is_valid(value):
                    return ObjectId(value)
                raise ValueError("ObjectID inválido")
            raise ValueError("Tipo inválido")
        
        return core_schema.with_info_plain_validator_function(validate)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: core_schema.CoreSchema, handler: Any) -> dict:
        return {"type": "string"}

class MongoObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        def validate(value: Any, info: core_schema.ValidationInfo) -> str:
            if isinstance(value, ObjectId):
                return str(value)
            if isinstance(value, str):
                if ObjectId.is_valid(value):
                    return value
                raise ValueError("ObjectID inválido")
            raise ValueError("Tipo inválido")
        
        return core_schema.with_info_plain_validator_function(validate)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: core_schema.CoreSchema, handler: Any) -> dict:
        return {"type": "string"}

__all__ = (
    "BaseModel",
    "Field",
    "ObjectId",
    "MongoObjectId",
    "PyObjectId",
    "List",
    "Dict",
    "Optional",
    "EmailStr",
)
