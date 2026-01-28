from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    
    # API Settings
    API_TITLE: str = "Community Helpdesk Chatbot API"
    API_VERSION: str = "2.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Ollama Settings - Using Llama 3.2 3B
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT: int = 120
    
    # ChromaDB Settings
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "community_services"
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # RAG Settings
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.0
    
    # Response Settings
    MAX_TOKENS: int = 500
    TEMPERATURE: float = 0.6
    
    # Location Settings
    DEFAULT_CITY: str = "Chennai"
    DEFAULT_STATE: str = "Tamil Nadu"
    
    # Customer Care Settings
    CUSTOMER_CARE_PHONE: str = "1913"
    CUSTOMER_CARE_EMAIL: str = "support@chennaicorporation.gov.in"
    CUSTOMER_CARE_HOURS: str = "24/7"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()