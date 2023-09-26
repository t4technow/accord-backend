from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from datetime import datetime
from django.db.models import Q, Max
from django.shortcuts import get_object_or_404

from .serializer import *
from chat.models import ChatMessage, ChatThread, GroupChatMessage, ChannelMessage
from chat.serializers import (
    ChatMessageSerializer,
    ChatThreadSerializer,
    GroupSerializer,
    GroupThreadSerializer,
    GroupMessageSerializer,
    ChannelMessageSerializer,
)
from social.models import Friend, FriendRequest, BlockedUser

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
import random

from notification.views import sendMessage


CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)


class ServerListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class UserServers(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        servers = Server.objects.filter(
            Q(owner__id=request.user.id) | Q(membership__id=request.user.id)
        ).distinct()
        serializer = ServerSerializer(servers, many=True)
        sendMessage()
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class ServerDetailView(RetrieveAPIView):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class ServerMembersListView(ListAPIView):
    queryset = Membership.objects.all()
    serializer_class = ServerMembersSerializer


class ServerCreationView(APIView):
    def post(self, request):
        category = request.data.get("category")
        name = request.data.get("name", None)
        avatar = request.FILES["avatar"]
        user = request.user
        try:
            new_server = Server.objects.create(
                owner=user, name=name, category=category, avatar=avatar
            )
            if new_server:
                Membership.objects.create(user=user, server=new_server, is_admin=True)
            new_server.save()
            serializer = ServerSerializer(new_server)
            return Response(status=status.HTTP_201_CREATED, data=serializer.data)
        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data="something went wrong"
            )


class ServerUpdateView(UpdateAPIView):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class ServerDeleteView(DestroyAPIView):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class ChannelListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, server_id):
        channels = Channel.objects.filter(server=server_id)
        serializer = ChannelSerializer(channels, many=True)

        return Response(serializer.data)


class ChannelDetailView(RetrieveAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class ChannelMessageView(ListAPIView):
    queryset = ChatMessage.objects.all()
    serializer_class = MessageSerializer


class ChannelCreateView(CreateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class ChannelUpdateView(UpdateAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class ChannelDeleteView(DestroyAPIView):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


# GROUPS
class GroupCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get("name", None)
        avatar = request.FILES["avatar"]
        owner = request.user
        description = request.data.get("description", None)
        members = request.data.getlist("members[]")

        if name:
            group = Group.objects.create(
                name=name, avatar=avatar, description=description
            )

        if group:
            GroupMembership.objects.create(user=owner, group=group, is_admin=True)

            for member in members:
                GroupMembership.objects.create(user_id=member, group=group)

            serializer = GroupSerializer(group)

            return Response(status=status.HTTP_201_CREATED, data=serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class GroupInfo(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupUpdateView(UpdateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GetGroupMembers(APIView):
    def get(self, request, *args, **kwargs):
        groupId = kwargs["group_id"]
        try:
            members = GroupMembership.objects.filter(group_id=groupId)
            serializer = GroupMembershipSerializer(members, many=True)
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data="error fetching group"
            )


class AddMemberToGroup(APIView):
    def post(self, request, **kwargs):
        group_id = kwargs["group_id"]
        members = request.data.get("members")
        try:
            group = Group.objects.get(id=group_id)
        except:
            group = None

        if group:
            for member in members:
                try:
                    user = User.objects.get(id=member)
                except:
                    user = None
                if user:
                    GroupMembership.objects.create(
                        user=user, group=group, is_admin=False
                    )
            return Response(
                status=status.HTTP_202_ACCEPTED, data="members added successfully"
            )
        return Response(status=status.HTTP_404_NOT_FOUND, data="group not found")


class GroupDeleteView(DestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class Login(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class Register(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserListView(ListAPIView):
    queryset = User.objects.filter(is_active=True).distinct()
    serializer_class = UserSerializer


class UserDetails(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"user": request.user})
        return Response(serializer.data)


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        user_to_block = get_object_or_404(User, username=username)

        if request.user.is_blocked_by(user_to_block):
            return Response(
                {"detail": "You are already blocked by this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            BlockedUser.objects.create(user=request.user, blocked_user=user_to_block)
            return Response(
                {"detail": f"You have blocked {user_to_block.username}."},
                status=status.HTTP_200_OK,
            )


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        user_to_unblock = get_object_or_404(User, username=username)

        blocked_relationship = BlockedUser.objects.filter(
            user=request.user, blocked_user=user_to_unblock
        ).first()

        if blocked_relationship:
            blocked_relationship.delete()
            return Response(
                {"detail": f"You have unblocked {user_to_unblock.username}."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": "You haven't blocked this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BlockedUsersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        blocked_users = BlockedUser.objects.filter(user=request.user)
        serializer = UserSerializer(
            blocked_users.values_list("blocked_user", flat=True), many=True
        )
        return Response(serializer.data)


class FriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user.id
        friends = Friend.objects.filter(user=user)
        friend_of = Friend.objects.filter(friend=user)
        serializer = CombinedFriendSerializer(
            {"friends": friends, "friend_of": friend_of}
        )

        response_data = serializer.data["friends"] + serializer.data["friend_of"]

        return Response(response_data)


class AddFriend(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user = request.user
        try:
            friend = User.objects.get(id=user_id)
            connection = FriendRequest.objects.filter(
                Q(sender=user, receiver=friend) | Q(sender=friend, receiver=user)
            )
        except:
            connection = None

        if not connection:
            FriendRequest.objects.create(sender=user, receiver=friend)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(
                status=status.HTTP_409_CONFLICT,
                data=f"request is already made",
            )


class PendingFriendRequests(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        sended_requests = FriendRequest.objects.filter(sender=user, status="pending")
        received_request = FriendRequest.objects.filter(receiver=user, status="pending")

        if sended_requests.exists() or received_request.exists():
            serializer = FriendRequestSerializer(
                {"sended": sended_requests, "received": received_request}
            )
            response_data = serializer.data["sended"] + serializer.data["received"]
            return Response(status=status.HTTP_200_OK, data=response_data)
        return Response(status=status.HTTP_204_NO_CONTENT, data="empty")


class AcceptFriendRequest(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, friend_id):
        user = User.objects.get(id=request.user.id)
        friend = User.objects.get(id=friend_id)
        friend_request = FriendRequest.objects.filter(
            sender=friend, receiver=user
        ).first()
        if friend_request:
            friend_request.status = "accepted"
            friend_request.save()
            Friend.objects.create(user=friend, friend=user)

            # TODO: send notification to the sender of this accepted request

            serializer = UserSerializer(
                friend, context={"user": request.user}, include_context=False
            )
            return Response(status=status.HTTP_202_ACCEPTED, data=serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST, data="something went wrong")


class ExploreListView(ListAPIView):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class ExploreCategory(RetrieveAPIView):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class MutualFriendsAPIView(APIView):
    def get(self, request, friend_id):
        user1 = User.objects.get(id=request.user.id)
        user2 = User.objects.get(id=friend_id)

        user1_friends = [
            friend.user if friend.friend == user1 else friend.friend
            for friend in Friend.objects.filter(Q(user=user1) | Q(friend=user1))
        ]
        user2_friends = [
            friend.user if friend.friend == user2 else friend.friend
            for friend in Friend.objects.filter(Q(user=user2) | Q(friend=user2))
        ]
        mutual_friends = set(user1_friends).intersection(user2_friends)

        serializer = UserSerializer(
            mutual_friends,
            many=True,
            context={"user": request.user},
            include_context=False,
        )

        return Response(serializer.data)


class SearchUsersAndServers(APIView):
    def get(self, request, **kwargs):
        user = request.user
        query = kwargs["query"]
        users = User.objects.filter(username__icontains=query)

        user_data = UserSerializer(
            users, many=True, context={"user": user}, include_context=True
        )
        return Response(status=status.HTTP_200_OK, data=user_data.data)


class GetChatThreads(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user.id
        self.queryset = ChatThread.objects.by_user(user=user)

        if not self.queryset.exists():
            return Response(status=status.HTTP_200_OK, data="empty")

        sender = (
            ChatThread.objects.filter(sender=user)
            .exclude(Q(sender=user, receiver=user))
            .annotate(latest_message=Max("chat_message_thread__timestamp"))
            .order_by("-latest_message")
            .distinct()
        )
        receiver = (
            ChatThread.objects.filter(receiver=user)
            .exclude(Q(sender=user, receiver=user))
            .annotate(latest_message=Max("chat_message_thread__timestamp"))
            .order_by("-latest_message")
            .distinct()
        )

        # Fetch groups of the requesting user
        user_groups = (
            Group.objects.filter(members__id=user)
            .annotate(latest_message=Max("group_chat_messages__timestamp"))
            .order_by("-latest_message")
            .distinct()
        )

        # Serialize the chat threads and groups
        chat_thread_serializer = ChatThreadSerializer(
            {"sender": sender, "receiver": receiver}
        )
        group_serializer = GroupThreadSerializer(user_groups, many=True)

        # Combine the serialized data into the response
        combined_data = (
            chat_thread_serializer.data["sender"]
            + chat_thread_serializer.data["receiver"]
            + group_serializer.data
        )

        # Sort the combined_data based on the 'latest_message' field
        try:
            sorted_combined_data = sorted(
                combined_data,
                key=lambda x: x.get("latest_message", datetime.min),
                reverse=True,
            )
        except Exception as e:
            sorted_combined_data = combined_data

        return Response(status=status.HTTP_200_OK, data=sorted_combined_data)


class GetThreadMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        receiver_id = kwargs.get("receiver")

        # Try to retrieve messages from the cache first
        cache_key = f"chat_messages_{request.user.id}_{receiver_id}"
        cached_messages = cache.get(cache_key)

        # if cached_messages:
        #     return Response(status=status.HTTP_200_OK, data=cached_messages)

        thread = ChatThread.objects.filter(
            Q(sender=request.user, receiver_id=receiver_id)
            | Q(sender_id=receiver_id, receiver=request.user)
        ).first()

        if not thread:
            return Response(status=status.HTTP_200_OK, data=None)

        messages = thread.chat_message_thread.all().order_by("timestamp")
        serializer = ChatMessageSerializer(messages, many=True)
        for message in messages:
            if message.user == request.user:
                continue  # Skip messages sent by the requesting user
            if not message.is_read:
                message.is_read = True
                message.delivery_status = True
                message.save()

        cache.set(cache_key, serializer.data, CACHE_TTL)

        return Response(status=status.HTTP_200_OK, data=serializer.data)


class GetGroupMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        group_id = kwargs.get("group_id")

        # Try to retrieve messages from the cache first
        cache_key = f"group_messages_{request.user.id}_{group_id}"
        cached_messages = cache.get(cache_key)

        # if cached_messages:
        #     return Response(status=status.HTTP_200_OK, data=cached_messages)

        messages = GroupChatMessage.objects.filter(group=group_id).order_by("timestamp")
        serializer = GroupMessageSerializer(messages, many=True)

        cache.set(cache_key, serializer.data, CACHE_TTL)

        return Response(status=status.HTTP_200_OK, data=serializer.data)


class GetChannelMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        channel_id = kwargs.get("channel_id")

        messages = ChannelMessage.objects.filter(channel=channel_id).order_by(
            "timestamp"
        )
        serializer = ChannelMessageSerializer(messages, many=True)

        return Response(status=status.HTTP_200_OK, data=serializer.data)


class FriendSuggestionAPIView(APIView):
    def get_mutual_friends(self, user1, user2):
        user1_friends = [
            friend.user if friend.friend == user1 else friend.friend
            for friend in Friend.objects.filter(Q(user=user1) | Q(friend=user1))
        ]
        user2_friends = [
            friend.user if friend.friend == user2 else friend.friend
            for friend in Friend.objects.filter(Q(user=user2) | Q(friend=user2))
        ]
        mutual_friends = set(user1_friends).intersection(user2_friends)
        return set(mutual_friends)

    def get_chat_thread_users(self, user):
        chat_threads = ChatThread.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values_list("sender", "receiver")

        chat_thread_users = set()
        for sender, receiver in chat_threads:
            if sender != user:
                chat_thread_users.add(sender)
            if receiver != user:
                chat_thread_users.add(receiver)

        return chat_thread_users

    def get(self, request, *args, **kwargs):
        user = request.user

        # Get user's friends
        user_friends = [
            friend.user if friend.friend == user else friend.friend
            for friend in Friend.objects.filter(Q(user=user) | Q(friend=user))
        ]

        # Get user's friend requests
        user_send_requests = FriendRequest.objects.filter(sender=user).values_list(
            "receiver", flat=True
        )
        user_received_requests = FriendRequest.objects.filter(
            receiver=user
        ).values_list("sender", flat=True)

        user_friend_requests = list(user_send_requests) + list(user_received_requests)

        if not user_friends and not user_friend_requests:
            # If user has no friends or accepted friend requests, suggest random users
            all_users_except_current = User.objects.filter(is_active=True).exclude(
                id=user.id
            )
            suggestions = random.sample(
                list(all_users_except_current),
                min(10, all_users_except_current.count()),
            )
        else:
            # Calculate common interests
            common_interests = set()

            for friend in user_friends:
                for friend2 in user_friends:
                    if friend != friend2:
                        mutual_friends = self.get_mutual_friends(friend, friend2)
                        common_interests.update(mutual_friends)

            filtered_common_interest = [
                friend
                for friend in common_interests
                if friend != user
                and friend not in user_friends
                and friend.id not in user_friend_requests
            ]

            if not filtered_common_interest:
                # If no common interests, suggest friends of friends in chat thread
                chat_thread_users = self.get_chat_thread_users(user)
                if chat_thread_users:
                    suggestions = user.get_friends_with_chat_thread_connections(
                        chat_thread_users
                    )
                    if not suggestions:
                        # Exclude user's friends from suggestions
                        all_users_except_current = (
                            User.objects.filter(is_active=True)
                            .exclude(id=user.id)
                            .exclude(id__in=[friend.id for friend in user_friends])
                            .exclude(id__in=[id for id in user_friend_requests])
                        )
                        suggestions = random.sample(
                            list(all_users_except_current),
                            min(10, all_users_except_current.count()),
                        )

                else:
                    all_users_except_current = (
                        User.objects.filter(is_active=True)
                        .exclude(id=user.id)
                        .exclude(id__in=[friend.id for friend in user_friends])
                        .exclude(id__in=[id for id in user_friend_requests])
                    )
                    suggestions = random.sample(
                        list(all_users_except_current),
                        min(10, all_users_except_current.count()),
                    )

            else:
                suggestions = filtered_common_interest

        suggestion = UserSerializer(suggestions, many=True)
        return Response(suggestion.data, status=status.HTTP_200_OK)


class GetUserInfo(APIView):
    def get(self, request, user_list):
        user = request.user
        friends = Friend.objects.filter(user=user)
        friend_of = Friend.objects.filter(friend=user)

        users = []
        for friend_id in user_list:
            try:
                friend_id = int(friend_id)
            except ValueError:
                continue  # Skip invalid IDs

            if friend_id in friends.values_list(
                "friend", flat=True
            ) or friend_id in friend_of.values_list("user", flat=True):
                user_info = User.objects.get(id=friend_id)
                users.append(user_info)

        user_data = UserSerializer(
            users, many=True, context={"user": user}, include_context=False
        ).data
        return Response(user_data, status=status.HTTP_200_OK)
