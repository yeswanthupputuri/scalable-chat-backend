from celery import shared_task

from .models import Notification


@shared_task
def send_notification(user_id, message_id):

    print(
        f"Processing notification for "
        f"user {user_id}, "
        f"message {message_id}"
    )

    notification = Notification.objects.filter(
        user_id=user_id,
        message_id=message_id,
        notification_type="MESSAGE"
    ).first()

    if notification is None:

        print(
            "Notification does not exist."
        )

        return

    print(
        f"Notification {notification.id} "
        f"processed successfully."
    )

    return notification.id