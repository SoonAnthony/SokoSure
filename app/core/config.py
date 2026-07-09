from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    AT_USERNAME: str
    AT_API_KEY: str
    AT_SHORTCODE: str = "42303"
    GEMINI_API_KEY: str  # Google Gemini API key

    class Config:
        env_file = ".env"


settings = Settings()