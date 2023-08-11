import os
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChatMessage, generate_thumbnail, GroupChatMessage, CallLog

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.dispatch import receiver
from django.db.models.signals import post_save

from datetime import datetime


@receiver(post_save, sender=ChatMessage)
def generate_thumbnail_after_save(sender, instance, created, **kwargs):
    if created and instance.file and instance.file_type == "application":
        # Generate the thumbnail for the uploaded file
        thumbnail_path = generate_thumbnail(instance.file.path)

        if thumbnail_path:
            thumbnail_filename = os.path.basename(thumbnail_path)

            with open(thumbnail_path, "rb") as f:
                # Use Django's File class to save the thumbnail to the file_thumb field
                thumbnail_file = File(f)
                instance.file_thumb.save(thumbnail_filename, thumbnail_file, save=False)

            # Save the model instance again to update the file_thumb field
            instance.save()


@receiver(post_save, sender=GroupChatMessage)
def generate_thumbnail_after_save_group(sender, instance, created, **kwargs):
    if created and instance.file:
        # Generate the thumbnail for the uploaded file
        thumbnail_path = generate_thumbnail(instance.file.path)

        if thumbnail_path:
            thumbnail_filename = os.path.basename(thumbnail_path)

            with open(thumbnail_path, "rb") as f:
                # Use Django's File class to save the thumbnail to the file_thumb field
                thumbnail_file = File(f)
                instance.file_thumb.save(thumbnail_filename, thumbnail_file, save=False)

            # Save the model instance again to update the file_thumb field
            instance.save()


@receiver(post_save, sender=CallLog)
def send_notification(sender, instance, **kwargs):
    # Send a notification to the WebSocket consumer group for the receiver
    channel_layer = get_channel_layer()
    caller_id = str(instance.call_from.id)
    receiver_id = str(instance.call_to.id)
    async_to_sync(channel_layer.group_send)(
        receiver_id,
        {
            "type": "send_notification",
            "message": {
                "title": "Incoming video call"
                if instance.type == "video"
                else "Incoming call",
                "sender_id": caller_id,
                "sender": str(instance.call_from.username),
                "type": str(instance.type),
            },
            "recipient_user_id": receiver_id,
        },
    )
