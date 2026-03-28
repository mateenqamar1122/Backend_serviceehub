"""
Database initialization script for creating tables using Alembic migrations.
"""
import asyncio
import logging

from app.db import engine, Base
from app.models import User, Service, Booking

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise


async def drop_db() -> None:
    """Drop all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("✅ Database tables dropped successfully")
    except Exception as e:
        logger.error(f"❌ Error dropping database tables: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())

