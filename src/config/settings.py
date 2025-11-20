"""Application settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Telegram API credentials
    telegram_api_id: int = Field(..., description="Telegram API ID")
    telegram_api_hash: str = Field(..., description="Telegram API Hash")
    telegram_phone: str = Field(..., description="Telegram phone number")
    telegram_password: str = Field(default="", description="Telegram 2FA password (if enabled)")
    
    # Supabase configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon/service key")
    
    # Supabase PostgreSQL direct connection (optional, for SQLAlchemy)
    supabase_user: str = Field(default="postgres", description="Supabase PostgreSQL user")
    supabase_password: str = Field(default="", description="Supabase PostgreSQL password")
    supabase_host: str = Field(default="", description="Supabase PostgreSQL host")
    supabase_port: int = Field(default=5432, description="Supabase PostgreSQL port")
    supabase_db: str = Field(default="postgres", description="Supabase PostgreSQL database name")
    
    # Database settings
    database_echo: bool = Field(default=False, description="Echo SQL queries")
    environment: str = Field(default="development", description="Environment (development, production, test)")
    
    # LLM configuration (ProxyAPI)
    llm_provider: str = Field(default="proxyapi", description="LLM provider name")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_api_key: str = Field(..., description="LLM API key")
    llm_base_url: str = Field(default="https://api.proxyapi.ru/openai/v1", description="LLM API base URL")
    
    # LLM Behavior
    llm_temperature: float = Field(default=0.6, description="LLM temperature (0.0-1.0), increased for better flexibility")
    llm_max_tokens: int = Field(default=512, description="Maximum tokens per request")
    llm_max_retries: int = Field(default=3, description="Maximum retry attempts")
    llm_timeout_seconds: int = Field(default=30, description="Request timeout in seconds")
    llm_batch_size: int = Field(default=10, description="Batch size for batch processing")
    
    # LLM Budgeting
    llm_daily_budget_usd: float = Field(default=10.0, description="Daily budget limit in USD")
    llm_analysis_threshold: float = Field(default=0.5, description="Minimum confidence for saving to DB")
    
    # LLM Performance
    llm_enable_caching: bool = Field(default=True, description="Enable response caching")
    llm_cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    @property
    def telegram_credentials(self) -> dict:
        """Get Telegram credentials as dictionary."""
        return {
            "api_id": self.telegram_api_id,
            "api_hash": self.telegram_api_hash,
            "phone_number": self.telegram_phone,
        }


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()


if __name__ == "__main__":
    # Test settings loading
    try:
        settings = get_settings()
        print("✓ Settings loaded successfully")
        print(f"  Telegram API ID: {settings.telegram_api_id}")
        print(f"  Supabase URL: {settings.supabase_url}")
        print(f"  LLM Provider: {settings.llm_provider}")
        print(f"  Log Level: {settings.log_level}")
    except Exception as e:
        print(f"✗ Error loading settings: {e}")
        print("  Make sure .env file exists and contains all required variables")

