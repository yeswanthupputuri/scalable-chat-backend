from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Conversation,
    ConversationMember,
    Message,
    Notification,
)
from .serializers import (
    AddConversationMemberSerializer,
    ConversationSerializer,
    MessageSerializer,
    NotificationSerializer,
)
from .services import create_chat_message

User = get_user_model()


class ConversationListCreateView(generics.ListCreateAPIView):

    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            members__user=self.request.user
        ).distinct().order_by("-created_at")

    def perform_create(self, serializer):
        conversation = serializer.save()

        ConversationMember.objects.get_or_create(
            conversation=conversation,
            user=self.request.user
        )


class AddConversationMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id
        )

        is_member = ConversationMember.objects.filter(
            conversation=conversation,
            user=request.user
        ).exists()

        if not is_member:
            return Response(
                {
                    "detail": (
                        "You are not a member of "
                        "this conversation."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AddConversationMemberSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]

        user = get_object_or_404(
            User,
            id=user_id
        )

        member, created = ConversationMember.objects.get_or_create(
            conversation=conversation,
            user=user
        )

        if not created:
            return Response(
                {
                    "detail": (
                        "User is already a member "
                        "of this conversation."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "detail": "User added successfully.",
                "user_id": user.id,
                "conversation_id": conversation.id,
            },
            status=status.HTTP_201_CREATED
        )


class ConversationMessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation = get_object_or_404(
            Conversation,
            id=self.kwargs["conversation_id"]
        )

        is_member = ConversationMember.objects.filter(
            conversation=conversation,
            user=self.request.user
        ).exists()

        if not is_member:
            raise PermissionDenied(
                "You are not a member of this conversation."
            )

        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            "sender"
        ).order_by(
            "created_at"
        )


class ConversationMessageCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        content = request.data.get("content")

        try:
            message = create_chat_message(
                conversation_id=conversation_id,
                sender=request.user,
                content=content,
            )

        except Conversation.DoesNotExist:
            return Response(
                {
                    "detail": "Conversation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except PermissionError as error:
            return Response(
                {
                    "detail": str(error)
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        except ValidationError as error:
            return Response(
                {
                    "detail": error.message
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = MessageSerializer(message)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related(
            "message"
        ).order_by(
            "-created_at"
        )


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return Response(
            {
                "unread_count": unread_count
            },
            status=status.HTTP_200_OK
        )


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )

        if not notification.is_read:
            notification.is_read = True
            notification.save(
                update_fields=["is_read"]
            )

        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )