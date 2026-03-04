"""DevAgent main entry point and orchestration."""

import asyncio
import logging

from config.settings import Settings
from storage.db import Database
from tg_bot.bot import create_bot

logger = logging.getLogger(__name__)


async def run_agent():
    """Main entry point for the DevAgent."""
    settings = Settings.from_env()
    errors = settings.validate()
    if errors:
        for e in errors:
            logger.error(f"Config error: {e}")
        raise SystemExit(1)

    db = Database(settings.db_path)
    await db.connect()

    try:
        app = create_bot(settings)
        logger.info("DevAgent started. Polling for messages...")
        await app.run_polling()
    finally:
        await db.close()


def main():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
