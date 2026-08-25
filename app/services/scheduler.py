import logging
import uuid
from datetime import datetime

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class SchedulerService:
    async def create_job(
        self,
        name: str,
        url: str,
        schedule: str,
        body: dict = None,
        headers: dict = None,
    ) -> str:
        if settings.GCP_PROJECT_ID:
            from google.cloud import scheduler_v1

            client = scheduler_v1.CloudSchedulerClient()
            parent = f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.CLOUD_TASKS_LOCATION}"

            job = {
                "name": f"{parent}/jobs/{name}",
                "http_target": {
                    "http_method": scheduler_v1.HttpMethod.POST,
                    "uri": url,
                    "headers": headers or {"Content-Type": "application/json"},
                    "body": str(body or {}).encode() if body else b"",
                },
                "schedule": schedule,
            }

            try:
                response = client.create_job(parent=parent, job=job)
                logger.info("Created scheduler job: %s", response.name)
                return response.name
            except Exception as exc:
                logger.warning("Failed to create scheduler job: %s", exc)
                raise

        job_id = str(uuid.uuid4())
        logger.info(
            "Mock Scheduler create job: name=%s, schedule=%s, url=%s",
            name, schedule, url,
        )
        return f"local://scheduler/{job_id}"

    async def delete_job(self, job_name: str) -> bool:
        if settings.GCP_PROJECT_ID:
            from google.cloud import scheduler_v1

            client = scheduler_v1.CloudSchedulerClient()
            try:
                client.delete_job(name=job_name)
                logger.info("Deleted scheduler job: %s", job_name)
                return True
            except Exception as exc:
                logger.warning("Failed to delete scheduler job: %s", exc)
                return False

        logger.info("Mock Scheduler delete job: %s", job_name)
        return True

    async def list_jobs(self) -> list:
        if settings.GCP_PROJECT_ID:
            from google.cloud import scheduler_v1

            client = scheduler_v1.CloudSchedulerClient()
            parent = f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.CLOUD_TASKS_LOCATION}"
            jobs = client.list_jobs(parent=parent)
            return [{"name": job.name, "schedule": job.schedule} for job in jobs]

        logger.info("Mock Scheduler list jobs")
        return []


scheduler_service = SchedulerService()
