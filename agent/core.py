"""DevAgent main entry point and orchestration."""

import asyncio
import logging

from config.settings import Settings
from storage.db import Database
from tg_bot.bot import create_bot

logger = logging.getLogger(__name__)


async def _init_and_run():
    """Initialize DB, build the bot, and run polling."""
    settings = Settings.from_env()
    errors = settings.validate()
    if errors:
        for e in errors:
            logger.error(f"Config error: {e}")
        raise SystemExit(1)

    db = Database(settings.db_path)
    await db.connect()

    try:
        app = create_bot(settings, db=db)
        logger.info("DevAgent started. Polling for messages...")
        async with app:
            await app.updater.start_polling()
            await app.start()
            # Block until stopped (Ctrl+C)
            import signal
            stop_event = asyncio.Event()
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, stop_event.set)
                except NotImplementedError:
                    # Windows doesn't support add_signal_handler
                    pass
            try:
                await stop_event.wait()
            except KeyboardInterrupt:
                pass
            await app.updater.stop()
            await app.stop()
    finally:
        await db.close()


def main():
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(_init_and_run())
    except KeyboardInterrupt:
        logger.info("DevAgent stopped.")


if __name__ == "__main__":
    main()
