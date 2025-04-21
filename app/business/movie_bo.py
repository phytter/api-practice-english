from typing import List, Dict, Optional
from app.integration.connector import get_subtitle_movie_connector
from app.model import MovieSearchOut, MovieOut, MovieIn
from app.business.subtitles_bo import SubtitlesBussiness
from app.core.dialogues.domain.dialogue_entity import DialogueMovie
from app.core.movies.infra.database.repositories import MovieProcessedMongoRepository
from app.core.movies.application import MovieMapper
from app.core.dialogues.infra.database.repositories.dialogue_mongo_repo import DialogueMongoRepository

class MovieBusiness:
    subtitle_movie = get_subtitle_movie_connector()
    movie_repo = MovieProcessedMongoRepository()
    dialogue_repo = DialogueMongoRepository()

    @classmethod
    async def get_processed_movie(cls, imdb_id: str) -> Optional[MovieOut]:
        entity = await cls.movie_repo.find_by_imdb_id(imdb_id)
        return MovieMapper.to_dto(entity) if entity else None

    @classmethod
    async def store_processed_movie(cls, movie_data: MovieIn):
        entity = MovieMapper.to_entity(movie_data)
        if entity.id:
            await cls.movie_repo.update(entity.id, entity)
        else:
            await cls.movie_repo.create(entity)
    
    @classmethod
    async def search_movies(cls, query: str) -> List[MovieSearchOut]:
        return await cls.subtitle_movie.search_movies(query)

    @classmethod
    async def process_movie_dialogues(cls, imdb_id: str, language: str = "en") -> Dict:
        movie_entity = await cls.movie_repo.find_by_imdb_id(imdb_id)
        if movie_entity is None:
            movie_dto = await cls.subtitle_movie.get_subtitles(imdb_id, language)
            movie_entity = MovieMapper.to_entity(movie_dto)
            await cls.movie_repo.create(movie_entity)
        
        dialogue_movie = DialogueMovie(
            imdb_id=imdb_id,
            title=movie_entity.title,
            language=language
        )
            
        dialogue_entities = SubtitlesBussiness.process_subtitle_content(movie_entity.content, dialogue_movie)
        
        if dialogue_entities:
            saved_entities = await cls.dialogue_repo.create_many(dialogue_entities)
            dialogues_count = len(saved_entities)
        else:
            dialogues_count = 0

        return {"message": "Subtitles processed successfully", "dialogues_count": dialogues_count}
    
    @classmethod
    async def search_processed_movies(cls, search: Optional[str] = None, skip: int = 0, limit: int = 20) -> List[MovieOut]:
        filters = {}
        if search:
            filters["title"] = search
        
        entities = await cls.movie_repo.find_with_filters(filters, skip, limit)
        
        return [MovieMapper.to_dto(entity) for entity in entities]