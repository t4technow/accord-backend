import json
import base64
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Count
from datetime import datetime

from .models import *
from user.models import UserProfile

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def websocket_connect(self, event):
        # Get the query parameters from the scope
        query_params = self.scope["query_string"].decode("utf-8")
        parsed_params = parse_qs(query_params)

        # Get the token, chatType, and channel from the parsed query parameters
        chat_type = parsed_params.get("chatType", [None])[0]
        groupId = parsed_params.get("channel", [None])[0]

        if chat_type == "group":
            self.chat_room = f"group_chatroom_{groupId}"
        else:
            user = self.scope["user"]
            self.chat_room = f"user_chatroom_{user.id}"

        await self.channel_layer.group_add(self.chat_room, self.channel_name)
        await self.accept()

    async def websocket_receive(self, event):
        dmp = json.loads(event["text"])
        message = dmp.get("message")
        sender_id = dmp.get("sender")
        server = dmp.get("server")
        channel = dmp.get("channel")
        chatType = dmp.get("chatType")
        is_group_chat = dmp.get("is_group_chat")
        files = dmp.get("files", [])
        sender = await self.get_user(sender_id)

        if is_group_chat:
            group = await self.get_group(channel)
            user_profile = await self.get_user_profile(sender)
            if files:
                for file_data in files:
                    file_name = file_data.get("fileName")
                    file_type = file_data.get("fileType")
                    file_data = file_data.get("fileData")
                    binary_data = base64.b64decode(file_data)
                    file = ContentFile(binary_data, name=file_name)

                    await self.save_group_message(
                        group, sender, message, file, file_type
                    )
            else:
                await self.save_group_message(group, sender, message)

            response = {
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

            if files:
                for file_data in files:
                    file_name = file_data.get("fileName")
                    file_type = file_data.get("fileType")
                    file_data = file_data.get("fileData")
                    binary_data = base64.b64decode(file_data)
                    file = ContentFile(binary_data, name=file_name)
                await self.save_message(thread, sender, message, file, file_type)
            else:
                await self.save_message(thread, sender, message)
            self.user = self.scope["user"]
            t = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

            response = {
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

    async def send_chat_message(self, event):
        message = event["text"]
        await self.send(text_data=message)

    async def websocket_disconnect(self, event):
        print("disconnected", event)

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
    def save_message(self, thread, user, message, file=None, fileType=None):
        ChatMessage.objects.create(
            thread=thread, user=user, message=message, file=file, file_type=fileType
        )

    @database_sync_to_async
    def get_user_profile(self, user):
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = None

        return profile

    @database_sync_to_async
    def get_group(self, group_id):
        group = Group.objects.filter(id=group_id)
        if group.exists():
            group = group.first()
        else:
            group = None

        return group

    @database_sync_to_async
    def save_group_message(self, group, user, message, file=None, file_type=None):
        GroupChatMessage.objects.create(
            group=group, user=user, message=message, file=file, file_type=file_type
        )
