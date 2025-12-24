from fastapi_users.authentication import AuthenticationBackend

from .strategy import get_database_strategy,get_jwt_strategy
from .transport import bearer_transport

authentication_backend = AuthenticationBackend(
    name="access-tokens-db",
    # transport=cookie_transport,
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
    # get_strategy=get_database_strategy,
)
