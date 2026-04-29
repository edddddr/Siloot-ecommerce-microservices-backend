import logging
from users.common.messaging.rabbitmq import EventPublisher
from users.common.events.user_event import build_user_event


logger = logging.getLogger(__name__)


def log_login_attempt(email, success):
    logger.info(
        "Login attempt",
        extra={
            "email": email,
            "success": success,
        },
    )



def publish_user_created(user):
    publisher = EventPublisher()

    event = build_user_event(user, "user.created")

    publisher.publish("user.created", event)
    # publisher.close()


def publish_user_updated(user):
    publisher = EventPublisher()

    event = build_user_event(user, "user.updated")

    publisher.publish("user.updated", event)
    publisher.close()