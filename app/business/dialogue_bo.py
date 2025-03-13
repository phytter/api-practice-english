from typing import List
from app.model import DialogueOut, ObjectId
from app.integration.mongo import Mongo
from fastapi import HTTPException, status

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
    
    @classmethod
    async def show_dialogue (cls, dialogue_id: str) -> DialogueOut:
        dialogue = await Mongo.dialogues.find_one({"_id": ObjectId(dialogue_id)})
        if not dialogue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dialogue not found"
            )
        return DialogueOut(**dialogue)