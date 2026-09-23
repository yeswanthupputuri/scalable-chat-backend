from django.db import migrations


def populate_message_status_users(apps, schema_editor):
    MessageStatus = apps.get_model("chats", "MessageStatus")
    ConversationMember = apps.get_model("chats", "ConversationMember")

    statuses = MessageStatus.objects.filter(
        user__isnull=True
    )

    for status in statuses:
        message = status.message

        recipients = ConversationMember.objects.filter(
            conversation_id=message.conversation_id
        ).exclude(
            user_id=message.sender_id
        )

        recipients = list(recipients)

        if not recipients:
            raise Exception(
                f"No recipient found for MessageStatus {status.id}"
            )

        # Reuse the existing status for the first recipient.
        first_recipient = recipients[0]

        status.user_id = first_recipient.user_id
        status.save(update_fields=["user"])

        # Create additional status rows for remaining recipients.
        for recipient in recipients[1:]:
            MessageStatus.objects.create(
                message_id=status.message_id,
                user_id=recipient.user_id,
                delivered_at=status.delivered_at,
                read_at=status.read_at,
            )


def reverse_populate_message_status_users(apps, schema_editor):
    MessageStatus = apps.get_model("chats", "MessageStatus")

    statuses = MessageStatus.objects.all().order_by(
        "message_id",
        "id"
    )

    seen_messages = set()

    for status in statuses:
        if status.message_id in seen_messages:
            status.delete()
        else:
            seen_messages.add(status.message_id)
            status.user_id = None
            status.save(update_fields=["user"])


class Migration(migrations.Migration):

    dependencies = [
        ("chats", "0003_notification_messagestatus_user_and_more"),
    ]

    operations = [
        migrations.RunPython(
            populate_message_status_users,
            reverse_populate_message_status_users,
        ),
    ]