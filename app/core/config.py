from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    AT_USERNAME: str   # Africa's Talking username
    AT_API_KEY: str    # Africa's Talking API key
    AT_SHORTCODE: str = "42303"  # AT SMS shortcode

    class Config:
        env_file = ".env"


settings = Settings()