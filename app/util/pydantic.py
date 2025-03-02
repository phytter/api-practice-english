from typing import Any, Callable, Type

import pydantic

from app.model.base import ObjectIdStr
from pydantic.v1.json import ENCODERS_BY_TYPE


def register_encoder(object_type: Type[Any], encoder: Callable[[Any], Any]):
  ENCODERS_BY_TYPE[object_type] = encoder


def generate_projection_model(model_name, projection: dict = {}):

    fields = {}

    for field in projection.keys():
        fields[field] = (Any, pydantic.Field(None))

    fields["id"] = (
        ObjectIdStr,
        pydantic.Field(..., default_factory=ObjectIdStr, alias="_id"),
    )

    return pydantic.create_model(model_name, **fields)
