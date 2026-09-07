from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, ConversationMember, Message

User = get_user_model()

class ConversationUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
        ]

class ConversationSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'created_at',
            'members',
        ]

        read_only_fields = [
            'id',
            'created_at',
        ]

    def get_members(self, obj):
        memberships = obj.members.select_related('user').all()

        users = [
            membership.user
            for membership in memberships
        ]

        return ConversationUserSerializer(
            users,
            many=True
        ).data


class AddConversationMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "User does not exist."
            )

        return value

class MessageSerializer(serializers.ModelSerializer):
    sender = ConversationUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'content',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'sender',
            'created_at',
        ]