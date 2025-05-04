from abc import ABC, abstractmethod
from typing import Any
from app.core.common.domain.value_objects import Uuid

class Entity(ABC):
  id: Uuid

  @abstractmethod
  def entity_dump(cls) -> dict[str, Any]:
      pass
