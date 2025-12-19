from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)




class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False


class DatabaseConfig(BaseModel):
    url: str
    echo: bool = True
    future: bool = True


class UrlPrefix(BaseModel):
    prefix: str = "/api"
    test: str = "/test"
    posts: str = "/posts"
    recipes: str = "/recipes"
    cuisines: str = "/cuisines"  
    allergens: str = "/allergens"
    ingredients: str= "/ingredients"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    url: UrlPrefix = UrlPrefix()
    db: DatabaseConfig


settings = Settings()


