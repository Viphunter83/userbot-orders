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
    
    # LLM configuration
    llm_provider: str = Field(default="proxyapi", description="LLM provider name")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_api_key: str = Field(..., description="LLM API key")
    
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

