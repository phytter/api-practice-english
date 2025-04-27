from abc import ABC, abstractmethod
from typing import Any

class Entity(ABC):
  id: str

  @abstractmethod
  def entity_dump(cls) -> dict[str, Any]:
      pass
