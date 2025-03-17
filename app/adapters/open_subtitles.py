from typing import List
from app.integration.http_client import HttpClient
from app.core.config import settings
from app.core.ports import SubtitleMovies
from app.model import MovieSearchOut, MovieOut
from datetime import datetime

class OpenSubTitles(SubtitleMovies):
    api_key: str = settings.OPENSUBTITLES_API_KEY
    base_url: str = settings.OPENSUBTITLES_API_URL
    default_headers = {
        "Api-Key": settings.OPENSUBTITLES_API_KEY,
        "Content-Type": "application/json"
    }

    @classmethod
    async def search_movies(cls, query: str) -> List[MovieSearchOut]:

        async with HttpClient.session.get(
            f"{cls.base_url}/features",
            headers=cls.default_headers,
            params={
                "query": query,
                "type": "movie"
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [
                    MovieSearchOut(
                        title=item.get("attributes", {}).get("title"),
                        year=int(item.get("attributes", {}).get("year") or 0),
                        imdb_id=str(item.get("attributes", {}).get("imdb_id", "")),
                        feature_type=item.get("attributes", {}).get("feature_type", ""),
                        img_url=item.get("attributes", {}).get("img_url"),
                    )                    
                    for item in data.get("data", [])
                ]
            else:
                error_message = await response.text()
                raise Exception(f"Failed to search movies: {error_message}")

    @classmethod
    async def get_subtitles(cls, imdb_id: str, language: str = "en") -> MovieOut:

        params = {
            "imdb_id": imdb_id,
            "languages": language
        }

        async with HttpClient.session.get(
            f"{cls.base_url}/subtitles",
            headers=cls.default_headers,
            params=params
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get subtitles: {await response.text()}")
            
            data = await response.json()
            if not data.get("data"):
                raise Exception("No subtitles found")
            
            # Get the best rated subtitle
            subtitle = max(data["data"], key=lambda x: x.get("ratings", 0))
            file_id = subtitle["attributes"]["files"][0]["file_id"]

            # Download the subtitle file
            async with HttpClient.session.post(
                f"{cls.base_url}/download",
                headers=cls.default_headers,
                json={"file_id": file_id}
            ) as download_response:
                if download_response.status != 200:
                    raise Exception(f"Failed to download subtitle: {await download_response.text()}")
                
                download_data = await download_response.json()
                subtitle_url = download_data["link"]
                
                # Get the actual subtitle content
                async with HttpClient.session.get(subtitle_url) as content_response:
                    subtitle_content = await content_response.text()
                    
                    all_movie_info = subtitle["attributes"]

                    processed_data = MovieOut(
                        imdb_id = imdb_id,
                        content = subtitle_content,
                        all_movie_info = all_movie_info,
                        subtitle_id = all_movie_info["subtitle_id"],
                        title = all_movie_info["feature_details"]["title"],
                        year = all_movie_info["feature_details"]["year"],
                        feature_type = all_movie_info["feature_details"]["feature_type"],
                        upload_date = datetime.strptime(all_movie_info["upload_date"], '%Y-%m-%dT%H:%M:%S%z'),
                        machine_translated = all_movie_info["machine_translated"],
                        ai_translated = all_movie_info["ai_translated"],
                        language = all_movie_info["language"]
                    )
                
                    return processed_data