from typing import List, Dict, Optional
from app.model import DialogueOut
from app.integration.mongo import Mongo

class DialogueBusiness:

    @classmethod
    async def search_dialogues(
        cls,
        search: str,
        imdb_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[DialogueOut]:
        query = {}
        if search:
            query["$or"] = [
                {"movie.title": {"$regex": search, "$options": "i"}},
                {"lines.text": {"$regex": search, "$options": "i"}},
            ]
        if imdb_id:
            query["movie.imdb_id"] = imdb_id
        cursor = Mongo.dialogues.find(query).skip(skip).limit(limit)
        return [DialogueOut(**doc) async for doc in cursor]