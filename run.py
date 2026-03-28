"""Script to initialize and run the application."""
import asyncio
import logging

from app.db.init_db import init_db
from app.main import app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    """Initialize database and run application."""
    logger.info("🚀 Initializing ServiceHub API...")

    # Initialize database
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

    logger.info("✅ Initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())

