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

    def get_unread_count(self, instance):
        return instance.chat_message_thread.filter(read=False).count()

    class Meta:
        model = ChatThread
        fields = ["id", "username", "profile", "email", "unread_count"]

    def get_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data


class ReceiverSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="sender.id")
    username = serializers.CharField(source="sender.username")
    email = serializers.CharField(source="sender.email")
    profile = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    def get_unread_count(self, instance):
        return instance.chat_message_thread.filter(read=False).count()

    class Meta:
        model = ChatThread
        fields = ["id", "username", "profile", "email", "unread_count"]

    def get_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.id).first()
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
        fields = ["message", "sender", "receiver", "username", "timestamp"]

    def get_receiver(self, obj):
        return obj.thread.receiver.id if obj.thread and obj.thread.receiver else None
