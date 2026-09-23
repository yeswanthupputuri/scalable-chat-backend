from django.urls import path

from .views import (
    AddConversationMemberView,
    ConversationListCreateView,
    ConversationMessageCreateView,
    ConversationMessageListView,
    NotificationListView,
    NotificationMarkReadView,
    NotificationUnreadCountView,
)


urlpatterns = [
    path(
        "",
        ConversationListCreateView.as_view(),
        name="conversation-list-create",
    ),

    path(
        "<int:conversation_id>/members/",
        AddConversationMemberView.as_view(),
        name="conversation-add-member",
    ),

    path(
        "<int:conversation_id>/messages/",
        ConversationMessageListView.as_view(),
        name="conversation-messages",
    ),

    path(
        "<int:conversation_id>/messages/send/",
        ConversationMessageCreateView.as_view(),
        name="conversation-message-create",
    ),

    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notification-list",
    ),

    path(
        "notifications/unread-count/",
        NotificationUnreadCountView.as_view(),
        name="notification-unread-count",
    ),

    path(
        "notifications/<int:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
]