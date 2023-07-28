import json
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

from django.db.models import Q, Max

from .serializer import *
from chat.models import ChatMessage, ChatThread, GroupChatMessage
from chat.serializers import (
    ChatMessageSerializer,
    ChatThreadSerializer,
    GroupSerializer,
    GroupMessageSerializer,
)
from social.models import Friend, FriendRequest


class ServerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        servers = Server.objects.filter(owner__id=request.user.id)
        serializer = ServerSerializer(servers, many=True)
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
            print(e)
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data="error fetching group"
            )


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
        return Response(status=status.HTTP_400_BAD_REQUEST, data="empty")


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

            serializer = UserSerializer(friend)
            return Response(status=status.HTTP_202_ACCEPTED, data=serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST, data="something went wrong")


class ExploreListView(ListAPIView):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class ExploreCategory(RetrieveAPIView):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class DirectMessages(ListAPIView):
    queryset = ChatMessage.objects.all()
    serializer_class = MessageSerializer


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

        serializer = UserSerializer(mutual_friends, many=True)

        return Response(serializer.data)


class GetChatThreads(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user.id
        self.queryset = ChatThread.objects.by_user(user=user)

        if not self.queryset.exists():
            return Response(status=status.HTTP_200_OK, data="empty")

        sender = (
            ChatThread.objects.filter(sender=user)
            .annotate(latest_message=Max("chat_message_thread__timestamp"))
            .order_by("-latest_message")
            .distinct()
        )
        receiver = (
            ChatThread.objects.filter(receiver=user)
            .annotate(latest_message=Max("chat_message_thread__timestamp"))
            .order_by("-latest_message")
            .distinct()
        )
        # Fetch groups of the requesting user
        user_groups = Group.objects.filter(members__id=user)

        # Serialize the chat threads and groups
        chat_thread_serializer = ChatThreadSerializer(
            {"sender": sender, "receiver": receiver}
        )
        group_serializer = GroupSerializer(user_groups, many=True)

        # Combine the serialized data into the response
        response_data = (
            chat_thread_serializer.data["sender"]
            + chat_thread_serializer.data["receiver"]
        )
        response_data.extend(group_serializer.data)

        return Response(status=status.HTTP_200_OK, data=response_data)


class GetThreadMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        receiver_id = kwargs.get("receiver")
        thread = ChatThread.objects.filter(
            Q(sender=request.user, receiver_id=receiver_id)
            | Q(sender_id=receiver_id, receiver=request.user)
        ).first()

        if not thread:
            return Response(status=status.HTTP_200_OK, data=None)

        messages = thread.chat_message_thread.all()
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class GetGroupMessages(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        group_id = kwargs.get("group_id")

        messages = GroupChatMessage.objects.filter(group=group_id)
        serializer = GroupMessageSerializer(messages, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)
