"""Database connection and session management."""

import asyncio
from typing import AsyncGenerator, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class DatabaseManager:
    """
    Менеджер для управления подключением к Supabase.
    Поддерживает асинхронные операции и connection pooling.
    """
    
    _instance: Optional["DatabaseManager"] = None
    _engine: Optional[AsyncEngine] = None
    _session_maker: Optional[async_sessionmaker] = None
    
    def __new__(cls):
        """Singleton pattern для гарантированного единственного instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> None:
        """
        Инициализировать подключение к Supabase.
        Вызывать один раз при запуске приложения.
        """
        if self._engine is not None:
            logger.warning("DatabaseManager already initialized")
            return
        
        settings = get_settings()
        
        # Build Supabase DSN
        # Format: postgresql+asyncpg://user:password@host:port/database
        # Если пароль не указан, используем REST API подход
        if not settings.supabase_password or not settings.supabase_host:
            logger.warning(
                "Supabase PostgreSQL password/host not configured. "
                "Using REST API approach via supabase_client.py. "
                "For direct DB access, configure SUPABASE_PASSWORD and SUPABASE_HOST in .env"
            )
            return
        
        db_url = (
            f"postgresql+asyncpg://"
            f"{settings.supabase_user}:"
            f"{settings.supabase_password}@"
            f"{settings.supabase_host}:"
            f"{settings.supabase_port}/"
            f"{settings.supabase_db}"
        )
        
        try:
            # Создать async engine с оптимальными настройками
            self._engine = create_async_engine(
                db_url,
                echo=settings.database_echo,  # Логирование SQL запросов
                pool_size=20,  # Размер connection pool
                max_overflow=10,  # Максимум доп. соединений
                pool_pre_ping=True,  # Проверять соединения перед использованием
                pool_recycle=3600,  # Переиспользовать соединения каждый час
                # Использовать QueuePool для production, NullPool для тестов
                poolclass=NullPool if settings.environment == "test" else QueuePool,
            )
            
            # Создать session factory
            self._session_maker = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            
            logger.info(
                f"✓ Database connection initialized",
                extra={"host": settings.supabase_host, "db": settings.supabase_db}
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Корректно закрыть все соединения."""
        if self._engine:
            await self._engine.dispose()
            logger.info("✓ Database connections closed")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Получить асинхронную сессию БД.
        Использовать как dependency для других модулей.
        
        Пример:
            async with db.get_session() as session:
                user = await session.get(User, user_id)
        """
        if self._session_maker is None:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
        
        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database transaction error: {e}")
                raise
    
    async def create_tables(self) -> None:
        """Создать все таблицы (для development/testing)."""
        if self._engine is None:
            raise RuntimeError("DatabaseManager not initialized")
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✓ All tables created")
    
    async def drop_tables(self) -> None:
        """Удалить все таблицы (для cleaning между тестами)."""
        if self._engine is None:
            raise RuntimeError("DatabaseManager not initialized")
        
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("✓ All tables dropped")
    
    def is_initialized(self) -> bool:
        """Проверить, инициализирован ли DatabaseManager."""
        return self._engine is not None


# Global instance
db_manager = DatabaseManager()


async def check_connection() -> bool:
    """
    Check database connection.
    
    Returns:
        True if connection successful (either direct PostgreSQL or REST API)
    """
    try:
        # Try direct DB connection first
        if db_manager.is_initialized():
            try:
                # Use async generator properly
                async for session in db_manager.get_session():
                    try:
                        # Simple query to test connection
                        from sqlalchemy import text
                        result = await session.execute(text("SELECT 1"))
                        if result.scalar() == 1:
                            logger.info("✓ Database connection check: OK (direct PostgreSQL)")
                            return True
                    finally:
                        # Session is auto-committed/closed by the generator
                        pass
            except Exception as direct_error:
                logger.warning(f"Direct PostgreSQL connection failed: {direct_error}")
                logger.info("Falling back to REST API...")
                # Continue to REST API fallback
        
        # Fallback to REST API
        from src.database.supabase_client import get_supabase_client
        
        client = await get_supabase_client()
        try:
            is_healthy = await client.health_check()
            if is_healthy:
                logger.info("✓ Database connection check: OK (via REST API)")
                return True
            else:
                logger.error("✗ Database connection check: Failed (REST API)")
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
        await db_manager.initialize()
        result = await check_connection()
        if result:
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
        await db_manager.close()
    
    asyncio.run(test())
