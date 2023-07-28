from rest_framework import serializers
from .models import *
from user.models import UserProfile
from api.serializer import UserProfileSerializer, UserSerializer
from django.db.models import Count


class SenderSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="receiver.id")
    username = serializers.CharField(source="receiver.username")
    email = serializers.CharField(source="receiver.email")
    profile = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    chat_type = serializers.SerializerMethodField()

    def get_unread_count(self, instance):
        return instance.chat_message_thread.filter(read=False).count()

    def get_chat_type(self, obj):
        return "user"

    class Meta:
        model = ChatThread
        fields = ["id", "username", "profile", "email", "unread_count", "chat_type"]

    def get_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.receiver.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data


class ReceiverSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="sender.id")
    username = serializers.CharField(source="sender.username")
    email = serializers.CharField(source="sender.email")
    profile = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    chat_type = serializers.SerializerMethodField()

    def get_unread_count(self, instance):
        return instance.chat_message_thread.filter(read=False).count()

    def get_chat_type(self, obj):
        return "user"

    class Meta:
        model = ChatThread
        fields = ["id", "username", "profile", "email", "unread_count", "chat_type"]

    def get_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.sender.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data


class ChatThreadSerializer(serializers.Serializer):
    sender = SenderSerializer(many=True)
    receiver = ReceiverSerializer(many=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation

    class Meta:
        model = ChatThread
        fields = "__all__"


# class GenericChatThreadSerializer(serializers.ModelSerializer):
#     sender = UserSerializer()
#     receiver = UserSerializer()

#     class Meta:
#         model = ChatThread
#         fields = '__all__'


# class ChatMessageSerializer(serializers.ModelSerializer):

#     user = UserSerializer()
#     thread = GenericChatThreadSerializer()
#     timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%f")

#     class Meta:
#         model = ChatMessage
#         fields = '__all__'


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(source="user", read_only=True)
    receiver = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username")
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%f")

    class Meta:
        model = ChatMessage
        fields = [
            "message",
            "sender",
            "receiver",
            "username",
            "timestamp",
            "file",
            "file_type",
        ]

    def get_receiver(self, obj):
        return obj.thread.receiver.id if obj.thread and obj.thread.receiver else None


class GroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembership
        fields = ("group", "is_admin")


class GroupSerializer(serializers.ModelSerializer):
    # members = GroupMembershipSerializer(many=True, read_only=True)
    chat_type = serializers.SerializerMethodField()

    def get_chat_type(self, obj):
        return "group"

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "avatar",
            "chat_type",
        )


class GroupMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(source="user", read_only=True)
    username = serializers.CharField(source="user.username")
    profilePic = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%f")

    class Meta:
        model = GroupChatMessage
        fields = [
            "message",
            "sender",
            "username",
            "timestamp",
            "profilePic",
            "file",
            "file_type",
        ]

    def get_profilePic(self, obj):
        try:
            user_profile = UserProfile.objects.get(user=obj.user)
            return user_profile.avatar.url if user_profile.avatar else None
        except UserProfile.DoesNotExist:
            return None
