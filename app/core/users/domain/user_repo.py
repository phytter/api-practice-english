from typing import Optional
from app.core.common.domain.repository import Repository
from app.core.users.domain import UserEntity

class UserRepository(Repository[UserEntity]):

    async def find_by_google_id(self, google_id: str) -> Optional[UserEntity]:
        pass