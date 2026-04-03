"""
Background scheduler runner — the alarm clock that actually fires.

Runs as an async task alongside the Telegram bot. Every POLL_INTERVAL seconds,
it checks the scheduled_jobs table for due jobs and executes them.

Supported actions:
  - send_message: Send a Telegram message to the user
  - reminder: Same as send_message (just a reminder text)
  - recurring_task: Execute and reschedule based on recurrence_rule
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from telegram import Bot

from jarvis.config import settings
from jarvis.db.repositories import ScheduledJobRepo, ContactRepo

logger = logging.getLogger(__name__)

POLL_INTERVAL = 30  # seconds between checks

# IST = UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))


class SchedulerRunner:
    """Background job executor."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self._running = False
        self._task: asyncio.Task | None = None

    def start(self):
        """Start the background scheduler loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Scheduler runner started (polling every {POLL_INTERVAL}s)")

    async def stop(self):
        """Stop the scheduler loop gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler runner stopped")

    async def _run_loop(self):
        """Main loop — check for due jobs and execute them."""
        while self._running:
            try:
                await self._process_due_jobs()
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)

            await asyncio.sleep(POLL_INTERVAL)

    async def _process_due_jobs(self):
        """Find and execute all jobs that are due."""
        now = datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S")
        jobs = await ScheduledJobRepo.get_due_jobs(now)

        for job in jobs:
            try:
                await self._execute_job(job)
                await ScheduledJobRepo.mark_completed(job["id"])

                # Handle recurring jobs — reschedule the next occurrence
                if job.get("recurrence_rule"):
                    await self._reschedule(job)

                logger.info(f"Executed job #{job['id']}: {job['description']}")
            except Exception as e:
                await ScheduledJobRepo.mark_failed(job["id"])
                logger.error(f"Job #{job['id']} failed: {e}")

    async def _execute_job(self, job: dict):
        """Execute a single job based on its action_type."""
        action = job["action_type"]
        user_id = job["user_id"]
        payload = job.get("payload", {})

        if action in ("send_message", "reminder"):
            message = payload.get("message", job.get("description", "Reminder!"))

            # If targeting a contact, add their name
            contact_name = payload.get("contact_name", "")
            if contact_name and action == "send_message":
                # For now, send the message to the USER about the contact
                # (actual WhatsApp/SMS sending is a future feature)
                message = f"[Scheduled] {message}"

            # Send to the user's Telegram chat (user_id = chat_id for private chats)
            await self.bot.send_message(chat_id=int(user_id), text=message)

        elif action == "recurring_task":
            message = payload.get("message", job.get("description", "Recurring reminder!"))
            await self.bot.send_message(chat_id=int(user_id), text=f"[Reminder] {message}")

        else:
            logger.warning(f"Unknown action type: {action}")

    async def _reschedule(self, job: dict):
        """Create the next occurrence of a recurring job."""
        rule = job["recurrence_rule"]
        current_time = job["scheduled_at"]

        next_time = _calculate_next_occurrence(current_time, rule)
        if not next_time:
            logger.warning(f"Could not calculate next occurrence for rule: {rule}")
            return

        await ScheduledJobRepo.create(
            user_id=job["user_id"],
            action_type=job["action_type"],
            description=job.get("description", ""),
            payload=job.get("payload", {}),
            target_contact_id=job.get("target_contact_id"),
            scheduled_at=next_time,
            recurrence_rule=rule,
        )
        logger.info(f"Rescheduled recurring job: next at {next_time}")


def _calculate_next_occurrence(current_time_str: str, rule: str) -> str | None:
    """Calculate the next occurrence based on recurrence rule."""
    try:
        current = datetime.fromisoformat(current_time_str)
    except (ValueError, TypeError):
        return None

    if rule == "daily":
        next_dt = current + timedelta(days=1)
    elif rule.startswith("weekly"):
        next_dt = current + timedelta(weeks=1)
    elif rule.startswith("monthly"):
        # Simple: add ~30 days, snap to same day
        day = current.day
        if current.month == 12:
            next_dt = current.replace(year=current.year + 1, month=1, day=day)
        else:
            try:
                next_dt = current.replace(month=current.month + 1, day=day)
            except ValueError:
                # Handle months with fewer days
                next_dt = current.replace(month=current.month + 2, day=1)
    elif rule.startswith("yearly"):
        next_dt = current.replace(year=current.year + 1)
    else:
        return None

    return next_dt.strftime("%Y-%m-%dT%H:%M:%S")
