from fastapi_users.authentication import CookieTransport, BearerTransport

from config import settings


bearer_transport = BearerTransport(
    tokenUrl=settings.url.bearer_token_url,
)

cookie_transport = CookieTransport(
    cookie_max_age=settings.auth.cookie_max_age,
    cookie_secure=settings.auth.cookie_secure,
    cookie_samesite=settings.auth.cookie_samesite,
)
