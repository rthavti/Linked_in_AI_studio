from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.logger import logger
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.topic_repository import TopicRepository
from app.database import SessionLocal
from app.services.generation_service import GenerationService
from app.services.publish_service import PublishService


scheduler = BackgroundScheduler(
    timezone=settings.TIMEZONE
)


def schedule_jobs():
    session = SessionLocal()
    try:
        settings_repo = ScheduleRepository(session)
        schedule = settings_repo.get()

        if schedule is None:
            schedule = settings_repo.create_default()

        scheduler.remove_all_jobs()

        if schedule.morning_enabled:
            hour, minute = schedule.morning_time.split(":")

            scheduler.add_job(
                scheduled_linkedin_workflow,
                CronTrigger(hour=int(hour), minute=int(minute)),
                id="linkedin_morning_job",
                replace_existing=True,
            )

            logger.info(
                "Registered scheduler job: linkedin_morning_job at %s",
                schedule.morning_time,
            )

        if schedule.evening_enabled:
            hour, minute = schedule.evening_time.split(":")

            scheduler.add_job(
                scheduled_linkedin_workflow,
                CronTrigger(hour=int(hour), minute=int(minute)),
                id="linkedin_evening_job",
                replace_existing=True,
            )

            logger.info(
                "Registered scheduler job: linkedin_evening_job at %s",
                schedule.evening_time,
            )

        logger.info(
            "Scheduled jobs updated. Morning: %s %s, Evening: %s %s",
            schedule.morning_enabled,
            schedule.morning_time,
            schedule.evening_enabled,
            schedule.evening_time,
        )
    finally:
        session.close()


def scheduled_linkedin_workflow():
    logger.info("Starting scheduled LinkedIn workflow.")
    session = SessionLocal()

    try:
        publish_service = PublishService(session)
        processed = publish_service.process_due_queue()
        if processed:
            logger.info("Processed %s queued LinkedIn publish jobs.", processed)

        topic_repository = TopicRepository(session)
        topic = topic_repository.get_next_pending()

        if topic is None:
            logger.info("No pending topics available for scheduled job.")
            return

        generation_service = GenerationService(topic_repository, session)

        if generation_service.generate_for_topic(topic):
            logger.info("Scheduled LinkedIn post generated successfully.")
        else:
            logger.info("Scheduled LinkedIn post generation failed.")
    finally:
        session.close()


def start_scheduler():
    schedule_jobs()
    scheduler.start()
    logger.info("Scheduler started.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
