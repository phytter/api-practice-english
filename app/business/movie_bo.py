from typing import List, Dict, Optional
from app.integration.connector import get_subtitle_movie_connector
from app.model import MovieSearchOut, MovieOut, MovieIn
from app.business.subtitles_bo import SubtitlesBussiness
from app.integration import Mongo
from datetime import datetime, timedelta, timezone

class MovieBusiness:
    subtitle_movie = get_subtitle_movie_connector()

    async def _get_from_cache(imdb_id: str) -> Optional[MovieOut]:
        cache_item = await Mongo.movies_processed.find_one({
            "imdb_id": imdb_id,
        })
        return MovieOut(**cache_item) if cache_item else None

    async def _save_to_cache(movie_data: MovieIn):
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
        movie_subtitle = await cls._get_from_cache(imdb_id)
        if movie_subtitle is None:
            movie_subtitle = await cls.subtitle_movie.get_subtitles(imdb_id, language)
            await cls._save_to_cache(movie_subtitle)
        
        dialogues = SubtitlesBussiness.process_subtitle_content(movie_subtitle.content)

        movie_info = {
            "imdb_id": imdb_id,
            "title": movie_subtitle.title or "Unknown",
            "year": movie_subtitle.year,
            "language": language
        }
        
        for dialogue in dialogues:
            dialogue_doc = {
                **dialogue.model_dump(),
                "movie": movie_info
            }
            await Mongo.dialogues.insert_one(dialogue_doc)
        return {"message": "Subtitles processed successfully", "dialogues_count": len(dialogues)}