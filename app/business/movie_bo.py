from typing import List, Dict, Optional
from datetime import datetime, timezone
from app.integration.connector import get_subtitle_movie_connector
from app.model import MovieSearchOut, MovieOut, MovieIn
from app.business.subtitles_bo import SubtitlesBussiness
from app.integration import Mongo
from .base import cursor_to_list

class MovieBusiness:
    subtitle_movie = get_subtitle_movie_connector()

    async def get_processed_movie(imdb_id: str) -> Optional[MovieOut]:
        cache_item = await Mongo.movies_processed.find_one({
            "imdb_id": imdb_id,
        })
        return MovieOut(**cache_item) if cache_item else None

    async def store_processed_movie(movie_data: MovieIn):
        await Mongo.movies_processed.update_one(
            {"imdb_id": movie_data.imdb_id},
            {
                "$set": {
                    **movie_data.model_dump(),
                    "timestamp": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
    @classmethod
    async def search_movies(cls, query: str) -> List[MovieSearchOut]:
        return await cls.subtitle_movie.search_movies(query)

    @classmethod
    async def process_movie_dialogues (cls, imdb_id: str, language: str = "en") -> List[Dict]:
        movie_subtitle = await cls.get_processed_movie(imdb_id)
        if movie_subtitle is None:
            movie_subtitle = await cls.subtitle_movie.get_subtitles(imdb_id, language)
            await cls.store_processed_movie(movie_subtitle)
        
        dialogues = SubtitlesBussiness.process_subtitle_content(movie_subtitle.content)

        movie_info = {
            "imdb_id": imdb_id,
            "title": movie_subtitle.title or "Unknown",
            "year": movie_subtitle.year,
            "language": language
        }
        
        dialogue_docs = [
            {
                **dialogue.model_dump(),
                "movie": movie_info
            }
            for dialogue in dialogues
        ]
        
        if dialogue_docs:
            await Mongo.dialogues.insert_many(dialogue_docs)

        return {"message": "Subtitles processed successfully", "dialogues_count": len(dialogues)}
    
    @classmethod
    async def search_processed_movies(cls, search: Optional[str] = None, skip: int = 0, limit: int = 20) -> MovieOut:
        query = {}
        if search:
            query["title"] = {"$regex": search, "$options": "i"}
        cursor = Mongo.movies_processed.find(query).skip(skip).limit(limit)
        return await cursor_to_list(MovieOut, cursor)
