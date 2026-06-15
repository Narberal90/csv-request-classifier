from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    concurrency: int = 3
    max_retries: int = 3
    retry_delays: list[int] = [10, 30, 60]

    model_config = {
        "env_file": str(Path(__file__).parent.parent / ".env")
    }


settings = Settings()
