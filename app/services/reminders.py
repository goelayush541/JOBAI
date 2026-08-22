import uuid
from datetime import datetime
from app.config import get_settings

settings = get_settings()


class ReminderService:
    async def schedule_reminder(
        self,
        reminder_id: uuid.UUID,
        user_id: uuid.UUID,
        scheduled_at: datetime,
    ) -> str:
        if settings.GCP_PROJECT_ID:
            from google.cloud import tasks_v2
            client = tasks_v2.CloudTasksClient()
            parent = client.queue_path(
                settings.GCP_PROJECT_ID,
                settings.CLOUD_TASKS_LOCATION,
                settings.CLOUD_TASKS_QUEUE,
            )
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": f"https://{settings.GCP_PROJECT_ID}.uc.r.appspot.com/api/v1/reminders/process",
                    "headers": {"Content-Type": "application/json"},
                    "body": str(
                        {"reminder_id": str(reminder_id), "user_id": str(user_id)}
                    ).encode(),
                },
                "schedule_time": scheduled_at,
            }
            created_task = client.create_task(request={"parent": parent, "task": task})
            return created_task.name

        return f"local://reminder/{reminder_id}"


reminder_service = ReminderService()
