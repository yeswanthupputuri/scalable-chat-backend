# tasks.py for define background tasks

from celery import shared_task

@shared_task
def send_notification(user_id, message_id):

    print(
        f"Notification sent to user {user_id} "
        f"for message {message_id}"
    )