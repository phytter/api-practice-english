from app.core.config import settings
from app.adapters.open_subtitles import OpenSubTitles
from app.util.patterns import SubtitleMoviesEnum

def get_subtitle_movie_connector():
    if settings.MOVIE_SERVICE == SubtitleMoviesEnum.OPEN_SUBTITLES:
        return OpenSubTitles()
    else:
        raise ValueError("Invalid movie service configuration")
