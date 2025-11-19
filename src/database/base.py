"""Database base configuration using SQLAlchemy + asyncpg for Supabase."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from loguru import logger

from src.config.settings import get_settings
from src.utils.logger import setup_logger

# Base class for SQLAlchemy models
Base = declarative_base()

# Global engine and session factory
_engine = None
_session_factory = None


def get_database_url() -> str:
    """
    Build PostgreSQL connection URL for Supabase.
    
    Returns:
        PostgreSQL async connection URL
    """
    settings = get_settings()
    url = settings.supabase_url
    
    # Extract project reference from Supabase URL
    # Format: https://{project_ref}.supabase.co
    if url.startswith("https://"):
        url = url.replace("https://", "").replace(".supabase.co", "")
    
    # Build PostgreSQL connection string
    # Supabase uses format: postgresql://postgres:[PASSWORD]@db.{project_ref}.supabase.co:5432/postgres
    # For asyncpg we need: postgresql+asyncpg://...
    
    # Note: We'll use the REST API key approach, but for direct DB access we'd need DB password
    # For now, we'll use the connection pool URL format
    # In production, you'd get the DB password from Supabase dashboard
    
    # Since we only have the API key, we'll use Supabase REST API via httpx instead
    # This file sets up the structure for future direct DB access
    
    db_url = f"postgresql+asyncpg://postgres:[PASSWORD]@db.{url}.supabase.co:5432/postgres"
    
    logger.warning(
        "Direct database connection requires DB password from Supabase dashboard. "
        "Currently using REST API via supabase_client.py"
    )
    
    return db_url


def init_database() -> None:
    """Initialize database engine and session factory."""
    global _engine, _session_factory
    
    if _engine is None:
        settings = get_settings()
        setup_logger(log_level=settings.log_level)
        
        # For now, we'll use REST API approach
        # Direct DB connection requires DB password from Supabase dashboard
        logger.info("Database initialization: Using REST API approach")
        logger.info("For direct DB access, configure DB_PASSWORD in .env")
        
        # Uncomment when DB password is available:
        # db_url = get_database_url()
        # _engine = create_async_engine(
        #     db_url,
        #     poolclass=NullPool,
        #     echo=False,
        #     future=True,
        # )
        # _session_factory = async_sessionmaker(
        #     _engine,
        #     class_=AsyncSession,
        #     expire_on_commit=False,
        # )
        
        logger.info("✓ Database configuration ready (REST API mode)")


async def get_session() -> AsyncSession:
    """
    Get async database session.
    
    Returns:
        AsyncSession instance
        
    Note: Currently returns None as we're using REST API approach.
    For direct DB access, configure DB_PASSWORD in .env and uncomment engine creation.
    """
    if _session_factory is None:
        init_database()
    
    if _session_factory is None:
        raise RuntimeError(
            "Database session factory not initialized. "
            "Configure DB_PASSWORD in .env for direct DB access, "
            "or use REST API via supabase_client.py"
        )
    
    async with _session_factory() as session:
        yield session


async def check_connection() -> bool:
    """
    Check database connection.
    
    Returns:
        True if connection successful
    """
    try:
        # For REST API approach, we check via supabase_client
        from src.database.supabase_client import get_supabase_client
        
        client = await get_supabase_client()
        try:
            is_healthy = await client.health_check()
            if is_healthy:
                logger.info("✓ Database connection check: OK (via REST API)")
                return True
            else:
                logger.error("✗ Database connection check: Failed")
                return False
        finally:
            await client.close()
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


if __name__ == "__main__":
    """Test database connection."""
    import asyncio
    
    async def test():
        init_database()
        result = await check_connection()
        if result:
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
    
    asyncio.run(test())

