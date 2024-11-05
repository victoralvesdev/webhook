from pydantic_settings import BaseSettings


class _Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str
    MONGO_DB_NAME: str = ""

    # SMTP
    SMTP_HOST: str = "smtp-mail.outlook.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_FROM_NAME: str = "Kirvano"


Settings = _Settings(_env_file=".env")  # type: ignore
