from pydantic_settings import BaseSettings


class Config(BaseSettings):
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "username"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "database"

    class Config:
        case_sensitive = True


settings = Config()
