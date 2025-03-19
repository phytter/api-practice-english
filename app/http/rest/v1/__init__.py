from .health_rest import health_v1
from .auth_rest import auth_v1
from .movie_rest  import movie_v1
from .dialogue_rest  import dialogue_v1
from .user_rest import user_v1

__all__ = (
   'health_v1',
   'auth_v1',
   'movie_v1',
   'dialogue_v1',
   'user_v1',
)