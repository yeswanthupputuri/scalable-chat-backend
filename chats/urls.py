from django.urls import path

from .views import (
    AddConversationMemberView,
    ConversationListCreateView,
    ConversationMessageListView,
)


urlpatterns = [

    path(
        '',
        ConversationListCreateView.as_view(),
        name='conversation-list-create'
    ),

    path(
        '<int:conversation_id>/members/',
        AddConversationMemberView.as_view(),
        name='conversation-add-member'
    ),

    path(
        '<int:conversation_id>/messages/',
        ConversationMessageListView.as_view(),
        name='conversation-messages'
    ),
]

