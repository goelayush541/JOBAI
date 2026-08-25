import json
import logging
import uuid
from datetime import datetime

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class PubSubService:
    async def publish(self, topic: str, data: dict) -> str:
        if settings.GCP_PROJECT_ID:
            from google.cloud import pubsub_v1

            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(settings.GCP_PROJECT_ID, topic)
            future = publisher.publish(
                topic_path, json.dumps(data, default=str).encode("utf-8")
            )
            message_id = future.result()
            logger.info("Published to %s: message_id=%s", topic, message_id)
            return message_id

        message_id = str(uuid.uuid4())
        logger.info(
            "Mock PubSub publish to %s: message_id=%s, data_keys=%s",
            topic, message_id, list(data.keys()),
        )
        return message_id

    async def subscribe(self, topic: str, callback) -> None:
        if settings.GCP_PROJECT_ID:
            from google.cloud import pubsub_v1

            subscriber = pubsub_v1.SubscriberClient()
            subscription_path = subscriber.subscription_path(
                settings.GCP_PROJECT_ID, f"{topic}-sub"
            )

            def message_handler(message):
                data = json.loads(message.data.decode("utf-8"))
                callback(data)
                message.ack()

            subscriber.subscribe(subscription_path, callback=message_handler)
            logger.info("Subscribed to %s", topic)
            return

        logger.info("Mock PubSub subscribe to %s (no-op in local mode)", topic)


pubsub_service = PubSubService()
