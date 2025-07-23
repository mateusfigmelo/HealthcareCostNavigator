"""Configuration settings for the Healthcare Cost Navigator."""


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/healthcare_navigator"
    )

    # OpenAI
    openai_api_key: str = "your-openai-api-key-here"
    openai_model: str = "gpt-4o"

    # Application
    app_name: str = "Healthcare Cost Navigator"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
