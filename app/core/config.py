from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import  PostgresDsn,RedisDsn,computed_field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Qoneqt Agent Network"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    
    #Database postgres
    DB_USER : str
    DB_PASSWORD : str
    DB_HOST : str
    DB_PORT : int = 5432
    DB_NAME : str
    
    #Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    # RabbitMQ
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    
    # Ollama LLM
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    
    # HuggingFace (optional, for vLLM)
    HF_TOKEN: Optional[str] = None

    @computed_field
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/" 
        
    @computed_field
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()
    
