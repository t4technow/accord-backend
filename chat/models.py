import os
from django.db import models
from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_path
from django.contrib.auth import get_user_model
from django.db.models import Q

from server.models import Channel

User = get_user_model()


class Group(models.Model):
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to="avatar/group", null=True, blank=True)
    description = models.CharField(max_length=230, null=True, blank=True)
    members = models.ManyToManyField(User, through="GroupMembership")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="members")
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ---> {self.group.name}"


class ThreadManager(models.Manager):
    def by_user(self, **kwargs):
        user = kwargs.get("user")
        lookup = Q(sender=user) | Q(receiver=user)
        qs = self.get_queryset().filter(lookup).distinct()
        return qs


class ChatThread(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="thread_sender",
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="thread_receiver",
    )

    objects = ThreadManager()

    class Meta:
        unique_together = ["sender", "receiver"]

    def __str__(self):
        return f"{self.sender} - {self.receiver}"


def create_text_fallback_thumbnail(doc):
    # Create a blank image with white background
    width, height = 200, 150  # Set the dimensions for the thumbnail
    background_color = (255, 255, 255)
    thumbnail = Image.new("RGB", (width, height), background_color)
    # Add the text content to the image
    draw = ImageDraw.Draw(thumbnail)
    text = get_text_content_from_docx(doc)
    text_color = (0, 0, 0)  # Black text color

    try:
        # Try loading the specified font
        font = ImageFont.truetype("arial.ttf", 20)  # Change the font and size as needed
    except OSError:
        # If the specified font is not found, use a system font as fallback
        font = ImageFont.load_default()
    print(draw.keys())
    # Calculate the size of the text using the temporary font
    text_width, text_height = draw.textsize(text, font=font)

    # Calculate the position to center the text on the thumbnail
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw the text on the thumbnail
    draw.text((x, y), text, fill=text_color, font=font)

    return thumbnail


def get_text_content_from_docx(doc):
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)


# Function to generate the thumbnail URL
def generate_thumbnail(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":
        # Handle PDF files
        images = convert_from_path(file_path, dpi=200)
        thumbnail_path = file_path.replace(".pdf", "_thumbnail.jpg")

        if images:
            images[0].save(thumbnail_path, "JPEG")
            return thumbnail_path

    # elif file_extension == ".docx":
    #     # Handle DOCX files
    #     thumbnail_path = file_path.replace(".docx", "_thumbnail.jpg")
    #     doc = Document(file_path)

    #     # Look for images in the document's body and save the first image as the thumbnail
    #     found_image = False
    #     for rel in doc.part.rels:
    #         if "image" in doc.part.rels[rel].target_ref:
    #             found_image = True
    #             with open(thumbnail_path, "wb") as f:
    #                 f.write(doc.part.rels[rel].target_part.blob)

    #     # If no images found, create a fallback thumbnail with the text content
    #     if not found_image:
    #         fallback_thumbnail = create_text_fallback_thumbnail(doc)
    #         fallback_thumbnail.save(thumbnail_path)
    #         return thumbnail_path

    # elif file_extension == ".txt":
    #     # Handle TXT files (no thumbnail generation, just return the file path)
    #     return file_path, None, file_extension

    return None, None, file_extension


def user_upload_path(instance, filename):
    username = instance.user.username if instance.user else "default_user_uploads"
    file_type = instance.file_type if instance.file_type else None
    return os.path.join("user_uploads", username, file_type, f"{filename}")


def user_thumbnail_upload_path(instance, filename):
    username = instance.user.username if instance.user else "default_user_uploads"
    file_type = instance.file_type if instance.file_type else None
    return os.path.join("user_uploads", username, file_type, "thumbnails", filename)


class ChatMessage(models.Model):
    thread = models.ForeignKey(
        ChatThread,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="chat_message_thread",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=user_upload_path, blank=True, null=True)
    file_thumb = models.ImageField(
        upload_to=user_thumbnail_upload_path,
        null=True,
        blank=True,
        max_length=100,
    )
    file_name = models.CharField(max_length=300, null=True, blank=True)
    file_type = models.CharField(max_length=30, null=True, blank=True)
    file_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    delivery_status = models.BooleanField(default=False)

    def __str__(self):
        return f"in {self.thread} - {self.user} says, {self.message} ==> {self.is_read}"


def group_upload_path(instance, filename):
    group_name = instance.group.name if instance.group else "default_group"
    file_type = instance.file_type if instance.file_type else None
    return os.path.join("group_uploads", group_name, file_type, f"{filename}")


def group_thumbnail_upload_path(instance, filename):
    group = instance.group.name if instance.group else "default_group_uploads"
    file_type = instance.file_type if instance.file_type else None
    return os.path.join("group_uploads", group, file_type, "thumbnails", filename)


class GroupChatMessage(models.Model):
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="group_chat_messages",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=group_upload_path, blank=True, null=True)
    file_thumb = models.ImageField(
        upload_to=group_thumbnail_upload_path,
        null=True,
        blank=True,
        max_length=100,
    )
    file_name = models.CharField(max_length=300, null=True, blank=True)
    file_type = models.CharField(max_length=30, null=True, blank=True)
    file_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(
        User,
        through="GroupMessageReadInfo",
        related_name="read_group_messages",
        blank=True,
    )
    is_read = models.BooleanField(default=False)
    delivery_status = models.BooleanField(default=False)
    delivered_to = models.ManyToManyField(
        User,
        through="GroupMessageDeliveryInfo",
        related_name="delivered_group_messages",
        blank=True,
    )

    def __str__(self):
        return f"in {self.group} - {self.user} says, {self.message}"


class GroupMessageReadInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(GroupChatMessage, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message.id} - Read at: {self.read_at}"


class GroupMessageDeliveryInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(GroupChatMessage, on_delete=models.CASCADE)
    delivered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.message.id} - Delivered at: {self.delivered_at}"


class ChannelMessage(models.Model):
    channel = models.ForeignKey(
        Channel,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="channel_messages",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=group_upload_path, blank=True, null=True)
    file_thumb = models.ImageField(
        upload_to=group_thumbnail_upload_path,
        null=True,
        blank=True,
        max_length=100,
    )
    file_name = models.CharField(max_length=300, null=True, blank=True)
    file_type = models.CharField(max_length=30, null=True, blank=True)
    file_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    read_by = models.ManyToManyField(
        User, related_name="read_channel_messages", blank=True
    )
    delivery_status = models.BooleanField(default=False)

    def __str__(self):
        return f"in {self.channel} - {self.user} says, {self.message}"


class CallLog(models.Model):
    call_from = models.ForeignKey(
        User, related_name="send_call", on_delete=models.DO_NOTHING
    )
    call_to = models.ForeignKey(
        User, related_name="received_call", on_delete=models.DO_NOTHING
    )
    type = models.CharField(
        max_length=10,
        choices=[
            ("voice", "Voice"),
            ("video", "Video"),
        ],
    )
    time = models.DateTimeField(auto_now_add=True)
    duration = models.CharField(max_length=10, null=True, blank=True)
