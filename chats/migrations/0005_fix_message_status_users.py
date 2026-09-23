from django.db import migrations


def fix_message_status_users(apps, schema_editor):
    MessageStatus = apps.get_model("chats", "MessageStatus")
    ConversationMember = apps.get_model("chats", "ConversationMember")

    statuses = MessageStatus.objects.filter(
        user__isnull=True
    ).order_by("id")

    for status in statuses:
        message = status.message

        recipients = list(
            ConversationMember.objects.filter(
                conversation_id=message.conversation_id
            ).exclude(
                user_id=message.sender_id
            ).order_by("user_id")
        )

        if not recipients:
            raise Exception(
                f"No recipient found for MessageStatus {status.id}"
            )

        # Assign the first recipient to the existing status.
        first_recipient = recipients[0]

        status.user_id = first_recipient.user_id
        status.save(update_fields=["user"])

        # Create status rows for the remaining recipients.
        for recipient in recipients[1:]:
            MessageStatus.objects.create(
                message_id=status.message_id,
                user_id=recipient.user_id,
                delivered_at=status.delivered_at,
                read_at=status.read_at,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("chats", "0004_populate_message_status_users"),
    ]

    operations = [
        migrations.RunPython(
            fix_message_status_users,
            migrations.RunPython.noop,
        ),
    ]