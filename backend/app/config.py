from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    gemini_api_key: str
    database_url: str
    mlflow_tracking_uri: str
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "gemini-embedding-001"

    chunk_size: int = 400
    chunk_overlap: int = 80
    top_k: int = 5

settings = Settings()