import asyncio
import logging

from jarvis.config import settings
from jarvis.db.database import init_db, Database
from jarvis.agents.supervisor import build_supervisor
from jarvis.interfaces.telegram import create_bot_app


def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.LOG_LEVEL),
    )
    # Silence noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Initializing database...")
    await init_db()

    logger.info("Building supervisor and sub-agents...")
    build_supervisor()

    logger.info("Starting JARVIS...")
    app = create_bot_app()

    if settings.WEBHOOK_URL:
        # Webhook mode for EC2 deployment
        logger.info(f"Starting in webhook mode: {settings.WEBHOOK_URL}")
        await app.bot.set_webhook(settings.WEBHOOK_URL)
        await app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_url=settings.WEBHOOK_URL,
        )
    else:
        # Polling mode for local development
        logger.info("Starting in polling mode (local dev)...")
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("JARVIS is online! Send a message to your Telegram bot.")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
        finally:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            await Database.close()


if __name__ == "__main__":
    asyncio.run(main())
