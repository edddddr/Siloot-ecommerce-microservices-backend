from django.core.management.base import BaseCommand
from users.models import User
from users.common.events.user_event import build_user_event
from users.common.messaging.rabbitmq import EventPublisher


class Command(BaseCommand):
    help = "Publish user.created events for existing users"

    def handle(self, *args, **kwargs):
        publisher = EventPublisher()

        print("The users are publishing")

        users = User.objects.all()

        for user in users:
            event = build_user_event(user, "user.created")

            publisher.publish("user.created", event)

            self.stdout.write(self.style.SUCCESS(
                f"Published user.created for {user.id}"
            ))

        # publisher.close()

        self.stdout.write(self.style.SUCCESS("Done publishing all users"))