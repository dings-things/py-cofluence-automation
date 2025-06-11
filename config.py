from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    CONFLUENCE_API_TOKEN: str
    ROOT_PAGE_ID: str
    CONFLUENCE_BASE_URL: str
    WEEKLY_REPORT_WEBHOOK_URL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
