# signals.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Notification

from datetime import datetime


@receiver(post_save, sender=Notification)
def send_notification(sender, instance, **kwargs):
    # Send a notification to the WebSocket consumer group for the receiver
    channel_layer = get_channel_layer()
    user_id = str(instance.recipient.id)
    async_to_sync(channel_layer.group_send)(
        user_id,
        {
            "type": "send_notification",
            "message": {
                "title": instance.title,
                "content": instance.content,
                "sender": str(instance.sender.id),
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "chat_type": "user" if instance.type == "message" else "group",
            },
            "recipient_user_id": user_id,
        },
    )
