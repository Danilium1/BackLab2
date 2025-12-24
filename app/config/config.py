from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from typing import Literal




class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False


class DatabaseConfig(BaseModel):
    url: str
    echo: bool = True
    future: bool = True


class AuthConfig(BaseModel):
    cookie_max_age: int = 3600
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"


class AccessToken(BaseModel):
    lifetime_seconds: int = 3600
    reset_password_token_secret: str = "65d30fd9fe2b8592d95817b005c0e0184d5b952e33a09bae47d33cfc9052e371"
    verification_token_secret: str = "79afe877e9a5291f626b9f16266d06e77566bd5f1a7ddbf3b8729969e879b080"


class UrlPrefix(BaseModel):
    prefix: str = "/api"
    test: str = "/test"
    posts: str = "/posts"
    recipes: str = "/recipes"
    cuisines: str = "/cuisines"  
    allergens: str = "/allergens"
    ingredients: str = "/ingredients"
    auth: str = "/auth"
    users: str = "/users"

    @property
    def bearer_token_url(self) -> str:
        # api/auth/login
        parts = (self.prefix, self.auth, "/login")
        path = "".join(parts)
        return path.removeprefix("/")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    url: UrlPrefix = UrlPrefix()
    auth: AuthConfig = AuthConfig()
    db: DatabaseConfig
    access_token: AccessToken = AccessToken()


settings = Settings()


