import django

django.setup()

import json
import base64
import threading
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.consumer import AsyncConsumer

from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async, async_to_sync
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from datetime import datetime
import redis
import asyncio

from django.db.models import Q, F

from .models import *
from notification.models import Notification
from user.models import UserProfile
from server.models import Server, Channel, Membership

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

from concurrent.futures import ThreadPoolExecutor
from channels.layers import get_channel_layer

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)

User = get_user_model()


def run_in_background(func, *args, **kwargs):
    def thread_target():
        async_to_sync(func)(*args, **kwargs)

    thread = threading.Thread(target=thread_target)
    thread.start()


class ChatConsumer(AsyncWebsocketConsumer):
    async def websocket_connect(self, event):
        # Get the query parameters from the scope
        query_params = self.scope["query_string"].decode("utf-8")
        parsed_params = parse_qs(query_params)

        # Get the token, chatType, and channel from the parsed query parameters
        chat_type = parsed_params.get("chatType", [None])[0]
        groupId = parsed_params.get("channel", [None])[0]
        self.groupId = groupId
        self.user = self.scope["user"]

        if chat_type == "group":
            self.chat_room = f"group_chatroom_{groupId}"
        elif chat_type == "channel":
            self.chat_room = f"server_chatroom_{groupId}"
        else:
            self.chat_room = f"user_chatroom_{self.user.id}"

        await self.channel_layer.group_add(self.chat_room, self.channel_name)
        await self.accept()

    async def websocket_receive(self, event):
        dmp = json.loads(event["text"])
        message_type = dmp.get("message_type")

        if message_type == "chat":
            await self.handle_chat_message(dmp)
        elif message_type == "video_signal":
            await self.handle_video_signal(dmp)
        elif message_type == "typing_status":
            typing_status = dmp.get("type")

            if typing_status == "typing":
                await self.send_typing_status()

    async def handle_chat_message(self, dmp):
        message = dmp.get("message")
        sender_id = dmp.get("sender")
        server = dmp.get("server")
        channel = dmp.get("channel")
        chatType = dmp.get("chatType")
        is_group_chat = dmp.get("is_group_chat")
        files = dmp.get("files", [])
        sender = await self.get_user(sender_id)

        if chatType == "group":
            group = await self.get_group(channel)
            user_profile = await self.get_user_profile(sender)

            group_members = await self.get_group_members(group)
            type = "group_message"
            for member in group_members:
                if member != sender:
                    recipient = member
                    title = f"{sender.username} in {group.name}"
                    content = message if message is not None else "file"

                    await self.create_notification(
                        recipient, title, content, sender, type
                    )

            group_cache_key = f"group_messages_{self.user.id}_{self.groupId}"
            group_messages = cache.get(group_cache_key) or []

            if files:
                for file_data in files:
                    file_name = file_data.get("fileName")
                    file_type = file_data.get("fileType")
                    file_data = file_data.get("fileData")
                    binary_data = base64.b64decode(file_data)
                    file = ContentFile(binary_data, name=file_name)

                    await self.save_group_message(
                        group, sender, message, file, file_type, file_name
                    )

                    # group_messages.append(
                    #     {
                    #         "group": group,
                    #         "sender": sender,
                    #         "message": message,
                    #         "file": file,
                    #         "file_type": file_type,
                    #         "file_name": file_name,
                    #         "timestamp": datetime.now().strftime(
                    #             "%Y-%m-%dT%H:%M:%S.%f"
                    #         ),
                    #     }
                    # )
                    # cache.set(group_cache_key, group_messages, CACHE_TTL)
            else:
                await self.save_group_message(group, sender, message)
                # group_messages.append(
                #     {
                #         "group": group,
                #         "sender": sender,
                #         "message": message,
                #         "file": None,
                #         "file_type": None,
                #         "file_name": None,
                #         "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                #     }
                # )
                # cache.set(group_cache_key, group_messages, CACHE_TTL)

            response = {
                "message_type": "chat",
                "message": message,
                "files": files,
                "sender": sender.id,
                "username": sender.username,
                "profile_pic": user_profile.avatar.url if user_profile.avatar else None,
                "group": group.id,
                "group_name": group.name,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "is_group_chat": True,
            }

            await self.channel_layer.group_send(
                f"group_chatroom_{channel}",
                {"type": "send_chat_message", "text": json.dumps(response)},
            )

        if chatType == "user":
            receiver = await self.get_user(channel)
            thread = await self.get_thread(sender, receiver)

            if not sender or not receiver:
                await self.send({"type": "websocket.send", "text": "User fetch error"})

            receiver_chat_room = f"user_chatroom_{channel}"

            if receiver != sender:
                recipient = receiver
                title = f"You have a new message from {sender.username}"
                content = message if message is not None else "file"

                await self.create_notification(recipient, title, content, sender)

            # chat_cache_key = f"chat_messages_{self.user.id}_{channel}"
            # chat_messages = cache.get(chat_cache_key) or []
            if sender and receiver:
                if files:
                    for file_data in files:
                        file_name = file_data.get("fileName")
                        file_type = file_data.get("fileType")
                        file_data = file_data.get("fileData")
                        binary_data = base64.b64decode(file_data)
                        file = ContentFile(binary_data, name=file_name)
                    await self.save_message(
                        thread, sender, message, file, file_type, file_name
                    )
                    # chat_messages.append(
                    #     {
                    #         "thread": thread.idzzt                       "sender": sender,
                    #         "message": message,
                    #         "file": file,
                    #         "file_type": file_type,
                    #         "file_name": file_name,
                    #         "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    #     }
                    # )
                    # cache.set(chat_cache_key, chat_messages, CACHE_TTL)

                else:
                    await self.save_message(thread, sender, message)

                # chat_messages.append(
                #     {
                #         "thread": thread.id,
                #         "sender": sender,
                #         "message": message,
                #         "file": None,
                #         "file_type": None,
                #         "file_name": None,
                #         "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                #     }
                # )
                # cache.set(chat_cache_key, chat_messages, CACHE_TTL)

            self.user = self.scope["user"]
            t = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

            response = {
                "message_type": "chat",
                "message": message,
                "sender": self.user.id,
                "username": self.user.username,
                "receiver": channel,
                "timestamp": t,
                "is_group_chat": False,
                "files": files,
            }

            await self.channel_layer.group_send(
                receiver_chat_room,
                {"type": "send_chat_message", "text": json.dumps(response)},
            )

            await self.channel_layer.group_send(
                self.chat_room,
                {"type": "send_chat_message", "text": json.dumps(response)},
            )

        if chatType == "channel":
            serverInstance = await self.get_server(server)
            channelInstance = await self.get_channel(channel)
            user_profile = await self.get_user_profile(sender)

            server_members = await self.get_server_members(server)
            type = "channel_message"
            for member in server_members:
                if member != sender:
                    recipient = member
                    title = f"{sender.username} in {serverInstance.name}"
                    content = message if message is not None else "file"

                    await self.create_notification(
                        recipient, title, content, sender, type
                    )

            if files:
                for file_data in files:
                    file_name = file_data.get("fileName")
                    file_type = file_data.get("fileType")
                    file_data = file_data.get("fileData")
                    binary_data = base64.b64decode(file_data)
                    file = ContentFile(binary_data, name=file_name)

                    await self.save_channel_message(
                        channelInstance, sender, message, file, file_type, file_name
                    )
            else:
                await self.save_channel_message(channelInstance, sender, message)

            response = {
                "message_type": "chat",
                "message": message,
                "files": files,
                "sender": sender.id,
                "username": sender.username,
                "profile_pic": user_profile.avatar.url if user_profile.avatar else None,
                "server": server,
                "channel_id": channel,
                "channel_name": channelInstance.name,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "is_group_chat": True,
            }

            await self.channel_layer.group_send(
                f"server_chatroom_{self.groupId}",
                {"type": "send_chat_message", "text": json.dumps(response)},
            )

    async def send_chat_message(self, event):
        message = event["text"]
        await self.send(text_data=message)

    async def handle_video_signal(self, data):
        signal_type = data.get("signal_type")
        sender_id = data.get("sender_id")
        signal_data = data.get("signal_data")
        receiver = data.get("receiver")

        receiver_chat_room = f"user_chatroom_{receiver}"

        if signal_type and sender_id and signal_data:
            await self.channel_layer.group_send(
                receiver_chat_room,
                {
                    "type": "send_video_signal",
                    "signal_type": signal_type,
                    "sender_id": sender_id,
                    "signal_data": signal_data,
                    "receiver": receiver,
                },
            )

    async def send_video_signal(self, event):
        signal_type = event["signal_type"]
        sender_id = event["sender_id"]
        signal_data = event["signal_data"]
        receiver = event["receiver"]

        response = {
            "message_type": "video_signal",
            "signal_type": signal_type,
            "sender_id": sender_id,
            "signal_data": signal_data,
            "receiver": receiver,
        }

        await self.send(text_data=json.dumps(response))

    async def send_typing_status(self):
        await self.channel_layer.group_send(
            "typing",
            {
                "type": "user_typing_status",
                "user_id": str(self.user.id),
                "typing": True,
            },
        )

    async def websocket_disconnect(self, event):
        print("disconnected", event)

    async def is_user_online(self, user_id):
        online_user_ids = await self.get_online_users_list()
        return str(user_id) in online_user_ids

    def get_redis_client(self):
        return redis.Redis(host="localhost", port=6379, db=0)

    async def get_online_user_ids(self):
        client = self.get_redis_client()
        online_user_ids = [
            user_id.decode() for user_id in client.zrangebyscore("online_users", 1, 1)
        ]
        return online_user_ids

    async def get_online_users_list(self):
        online_user_ids = await self.get_online_user_ids()
        return online_user_ids

    async def update_delivery_status(self, receiver):
        await self.mark_message_as_delivered(receiver)

    @database_sync_to_async
    def get_user_groups(self, user_id):
        user_groups = Group.objects.filter(groupmembership__user_id=user_id)
        return user_groups

    @database_sync_to_async
    def get_user_groups_messages(self, user_id):
        user_groups = Group.objects.filter(groupmembership__user_id=user_id)
        user_group_messages = GroupChatMessage.objects.filter(
            group__in=user_groups, delivery_status=False
        ).exclude(groupmessagedeliveryinfo__user_id=user_id)
        return user_group_messages

    @database_sync_to_async
    def get_undelivered_messages(self, user_id):
        undelivered_messages = ChatMessage.objects.filter(
            (Q(thread__sender_id=user_id) | Q(thread__receiver_id=user_id))
            & Q(delivery_status=False)
            & ~Q(user_id=user_id)
        )

        return list(undelivered_messages)  # Convert QuerySet to a list

    @database_sync_to_async
    def mark_messages_as_delivered(self, messages, group_messages, user_id):
        for message in messages:
            try:
                message.delivery_status = True
                message.save()
            except ValueError as e:
                raise e

        for message in group_messages:
            try:
                GroupMessageDeliveryInfo.objects.create(
                    user_id=user_id, message=message
                )
            except ValueError as e:
                raise e

    async def mark_message_as_delivered(self, user_id):
        group_messages = await self.get_user_groups_messages(user_id)

        undelivered_messages = await self.get_undelivered_messages(user_id)
        await self.mark_messages_as_delivered(
            undelivered_messages, group_messages, user_id
        )

    @database_sync_to_async
    def get_user(self, user_id):
        user = User.objects.filter(id=user_id)
        if user.exists():
            user = user.first()
        else:
            user = None

        return user

    @database_sync_to_async
    def get_thread(self, sender, receiver):
        thread = ChatThread.objects.filter(
            Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
        )
        if thread.exists():
            thread = thread.first()
        else:
            thread = ChatThread.objects.create(sender=sender, receiver=receiver)

        return thread

    @database_sync_to_async
    def save_message(
        self, thread, user, message, file=None, fileType=None, file_name=None
    ):
        ChatMessage.objects.create(
            thread=thread,
            user=user,
            message=message,
            file=file,
            file_type=fileType,
            file_name=file_name,
        )

    @database_sync_to_async
    def get_user_profile(self, user):
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = None

        return profile

    @database_sync_to_async
    def get_group_members(self, group):
        return [member for member in group.members.all()]

    @database_sync_to_async
    def get_group(self, group_id):
        group = Group.objects.filter(id=group_id)
        if group.exists():
            group = group.first()
        else:
            group = None

        return group

    @database_sync_to_async
    def save_group_message(
        self, group, user, message, file=None, file_type=None, file_name=None
    ):
        GroupChatMessage.objects.create(
            group=group,
            user=user,
            message=message,
            file=file,
            file_type=file_type,
            file_name=file_name,
        )

    @database_sync_to_async
    def get_server_members(self, server_id):
        memberships = Membership.objects.filter(server_id=server_id)
        return [member.user for member in memberships]

    @database_sync_to_async
    def get_server(self, server_id):
        server = Server.objects.filter(id=server_id)
        if server.exists():
            server = server.first()
        else:
            server = None

        return server

    @database_sync_to_async
    def get_channel(self, channel_id):
        channel = Channel.objects.filter(id=channel_id)
        if channel.exists():
            channel = channel.first()
        else:
            channel = None

        return channel

    @database_sync_to_async
    def save_channel_message(
        self, channel, user, message, file=None, file_type=None, file_name=None
    ):
        ChannelMessage.objects.create(
            channel=channel,
            user=user,
            message=message,
            file=file,
            file_type=file_type,
            file_name=file_name,
        )

    @database_sync_to_async
    def create_notification(self, recipient, title, content, sender, type="message"):
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            content=content,
            type=type,
            sender=sender,
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            user_id = str(self.scope["user"].id)
            await self.channel_layer.group_add(user_id, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            user_id = str(self.scope["user"].id)
            await self.channel_layer.group_discard(user_id, self.channel_name)

    async def send_notification(self, event):
        recipient_user_id = event["recipient_user_id"]

        if (
            self.scope["user"].is_authenticated
            and str(self.scope["user"].id) == recipient_user_id
        ):
            message = event["message"]

            await self.send(
                text_data=json.dumps(
                    {
                        "type": "notification",
                        "message": message,
                    }
                )
            )


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
            await self.channel_layer.group_add("online_users", self.channel_name)
            await self.accept()
            await self.update_online_status(True)
            await ChatConsumer.update_delivery_status(ChatConsumer(), self.user.id)

    async def disconnect(self, close_code):
        if hasattr(self, "user"):
            await self.update_online_status(False)
            await self.channel_layer.group_discard("online_users", self.channel_name)

    async def update_online_status(self, is_online):
        online_status = "online" if is_online else "offline"
        status_score = 1 if is_online else 0

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.update_status_in_redis, status_score)

        # Broadcast the updated online user IDs list to the entire group
        asyncio.create_task(self.broadcast_online_users_list())

    def update_status_in_redis(self, status_score):
        client = self.get_redis_client()
        client.zadd("online_users", {self.user.id: status_score})

    async def user_online_status(self, event):
        pass  # No individual user messages

    async def online_users_list(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "online_users_list",
                    "online_users": event["online_users"],
                }
            )
        )

    async def receive(self, text_data):
        # dmp = json.loads(event["text"])
        print("\n\n", text_data, "\n\n")
        pass  # You can

    def get_redis_client(self):
        return redis.Redis(host="localhost", port=6379, db=0)

    async def get_online_user_ids(self):
        client = self.get_redis_client()
        online_user_ids = [
            user_id.decode() for user_id in client.zrangebyscore("online_users", 1, 1)
        ]
        return online_user_ids

    async def broadcast_online_users_list(self):
        online_user_ids = await self.get_online_user_ids()
        await self.channel_layer.group_send(
            "online_users",
            {
                "type": "online_users_list",
                "online_users": online_user_ids,
            },
        )


class PeerConnectionConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        query_params = self.scope["query_string"].decode("utf-8")
        parsed_params = parse_qs(query_params)
        target = parsed_params.get("target", [None])
        user = self.scope["user"]

        self.chatroom = f"call_chatroom_{target[0]}"

        # Notify target user if they are online
        target_user_id = target[0]

        if user.id != int(target_user_id):
            await self.create_call_log(user, target_user_id, "video")

        await self.channel_layer.group_add(self.chatroom, self.channel_name)
        await self.send({"type": "websocket.accept"})

    async def websocket_disconnect(self, event):
        await self.channel_layer.group_send(
            self.chatroom,
            {"type": "chat_message", "text": json.dumps({"response": "user_left"})},
        )

    async def websocket_receive(self, event):
        json_dmp = json.loads(event["text"])
        data = json_dmp["message"]
        respo = {
            "response": data,
        }

        respo["user"] = self.scope["user"].id

        await self.channel_layer.group_send(
            self.chatroom, {"type": "chat_message", "text": json.dumps(respo)}
        )

    async def chat_message(self, event):
        await self.send({"type": "websocket.send", "text": event["text"]})

    @database_sync_to_async
    def create_call_log(self, caller, receiver, type):
        CallLog.objects.create(call_from=caller, call_to_id=receiver, type=type)
