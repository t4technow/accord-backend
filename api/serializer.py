from rest_framework import serializers
from server.models import Server, Channel, Membership
from user.models import User, UserProfile
from chat.models import ChatMessage, Group, GroupMembership
from social.models import Friend, FriendRequest

from django.conf import settings
from django.db.models import Q


class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = "__all__"

    def create(self, validated_data):
        return super().create(validated_data)


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = "__all__"


class ServerMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["phone_number", "avatar", "cover", "bio"]

    def get_avatar(self, obj):
        avatar_url = obj.avatar.url if obj.avatar else None
        if avatar_url:
            avatar_url = f"{settings.SITE_DOMAIN}{avatar_url}"
        return avatar_url

    def get_cover(self, obj):
        cover_url = obj.cover.url if obj.cover else None
        if cover_url:
            cover_url = f"{settings.SITE_DOMAIN}{cover_url}"
        return cover_url


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data

    class Meta:
        model = User
        fields = ["id", "email", "username", "profile", "date_joined"]


class MemberUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data

    class Meta:
        model = User
        fields = ["id", "email", "username", "profile", "date_joined"]


class FriendSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id")
    friend_id = serializers.IntegerField(source="friend.id")
    username = serializers.CharField(source="friend.username")
    friend_profile = serializers.SerializerMethodField()

    class Meta:
        model = Friend
        fields = ["id", "friend_id", "username", "friend_profile", "established_date"]

    def get_friend_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.friend.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data


class FriendOfSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="friend.id")
    friend_id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    friend_profile = serializers.SerializerMethodField()

    def get_friend_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.user.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data

    class Meta:
        model = Friend
        fields = ["id", "friend_id", "username", "friend_profile", "established_date"]


class CombinedFriendSerializer(serializers.Serializer):
    friends = FriendSerializer(many=True)
    friend_of = FriendOfSerializer(many=True)

    def to_representation(self, instance):
        friends_data = FriendSerializer(instance["friends"], many=True).data
        friend_of_data = FriendOfSerializer(instance["friend_of"], many=True).data
        return {"friends": friends_data, "friend_of": friend_of_data}


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["avatar"]


class MutualFriendsSerializer(serializers.ModelSerializer):
    friend = UserAvatarSerializer(source="friend.profile", read_only=True)
    id = serializers.IntegerField(source="friend.id")
    username = serializers.CharField(source="friend.username")

    class Meta:
        model = Friend
        fields = ["friend", "id", "username"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"


class GroupMembershipSerializer(serializers.ModelSerializer):
    user = MemberUserSerializer()

    class Meta:
        model = GroupMembership
        fields = ("user", "is_admin")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(data.pop("user"))
        return data


class SendRequestSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="sender.id")
    friend_id = serializers.IntegerField(source="receiver.id")
    username = serializers.CharField(source="receiver.username")
    friend_profile = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Friend
        fields = [
            "id",
            "friend_id",
            "username",
            "friend_profile",
            "established_date",
            "type",
        ]

    def get_friend_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.receiver.id).first()
        serializer = UserProfileSerializer(user)
        return serializer.data

    def get_type(self, obj):
        return "send"


class ReceivedRequestSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="receiver.id")
    friend_id = serializers.IntegerField(source="sender.id")
    username = serializers.CharField(source="sender.username")
    friend_profile = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_friend_profile(self, obj):
        user = UserProfile.objects.filter(user=obj.sender.id).first()
        serializer = UserProfileSerializer(user)

        return serializer.data

    def get_type(self, obj):
        return "received"

    class Meta:
        model = Friend
        fields = [
            "id",
            "friend_id",
            "username",
            "friend_profile",
            "established_date",
            "type",
        ]


class FriendRequestSerializer(serializers.Serializer):
    sended = SendRequestSerializer(many=True)
    receiver = ReceivedRequestSerializer(many=True)

    def to_representation(self, instance):
        sended_data = SendRequestSerializer(instance["sended"], many=True).data
        received_data = ReceivedRequestSerializer(instance["received"], many=True).data
        return {"sended": sended_data, "received": received_data}
