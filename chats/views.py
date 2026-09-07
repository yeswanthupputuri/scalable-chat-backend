from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, ConversationMember, Message
from .serializers import (
    AddConversationMemberSerializer,
    ConversationSerializer,
    MessageSerializer,
)

User = get_user_model()

class ConversationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            members__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        conversation = serializer.save()

        ConversationMember.objects.create(
            conversation=conversation,
            user=self.request.user
        )


class AddConversationMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):

        conversation = get_object_or_404(
            Conversation, id=conversation_id
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
                status=403
            )

        serializer = AddConversationMemberSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']

        user = get_object_or_404(
            User, id=user_id
        )

        member, created = ConversationMember.objects.get_or_create(
            conversation=conversation, user=user
        )

        if not created:
            return Response(
                {
                    "detail": (
                        "User is already a member "
                        "of this conversation."
                    )
                },
                status=400
            )

        return Response(
            {
                "detail": "User added successfully.",
                "user_id": user.id,
                "conversation_id": conversation.id,
            },
            status=201
        )


class ConversationMessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        conversation = get_object_or_404(
            Conversation,
            id=self.kwargs['conversation_id']
        )

        is_member = ConversationMember.objects.filter(
            conversation=conversation,
            user=self.request.user
        ).exists()

        if not is_member:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "You are not a member of this conversation."
            )

        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender'
        ).order_by(
            'created_at'
        )