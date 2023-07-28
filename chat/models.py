import os
from django.db import models
from docx import Document
from docx.shared import Inches
from pdf2image import convert_from_path
from django.contrib.auth import get_user_model
from django.db.models import Q

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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


# Function to generate the thumbnail URL
def generate_thumbnail(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":
        # Handle PDF files
        images = convert_from_path(file_path, dpi=200)
        thumbnail_path = file_path.replace(".pdf", "_thumbnail.jpg")

        if images:
            images[0].save(thumbnail_path, "JPEG")
            return thumbnail_path, "jpg", file_extension

    elif file_extension == ".docx":
        # Handle DOCX files
        thumbnail_path = file_path.replace(".docx", "_thumbnail.jpg")
        doc = Document(file_path)
        img = doc.inline_shapes[0].inline_graphic.graphic.graphicData.pic.blipFill.blip

        with open(thumbnail_path, "wb") as f:
            f.write(img.embed)

        return thumbnail_path, "jpg", file_extension

    elif file_extension == ".txt":
        # Handle TXT files (no thumbnail generation, just return the file path)
        return file_path, None, file_extension

    return None, None, file_extension


def user_upload_path(instance, filename):
    username = instance.user.username if instance.user else "default_user_uploads"
    file_type = instance.file_type if instance.file_type else None
    return os.path.join("user_uploads", username, file_type, f"{filename}")


def user_thumbnail_upload_path(instance, filename):
    username = instance.user.username if instance.user else "default_user_uploads"
    return os.path.join("user_uploads", username, "thumbnails", f"{filename}")


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
        upload_to=f"{user_upload_path}/thumbnails", null=True, blank=True
    )
    file_type = models.CharField(max_length=30, null=True, blank=True)
    file_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.file:
            # Generate the thumbnail for the uploaded file
            thumbnail_path = generate_thumbnail(self.file.path)

            if thumbnail_path:
                # Set the file_thumb field to the generated thumbnail URL
                self.file_thumb.save(
                    os.path.basename(thumbnail_path),
                    open(thumbnail_path, "rb"),
                    save=False,
                )

        super(ChatMessage, self).save(*args, **kwargs)

    def __str__(self):
        return f"in {self.thread} - {self.user} says, {self.message}"


def group_upload_path(instance, filename):
    group_name = instance.group.name if instance.group else "default_group"
    file_type = instance.file_type if instance.file_type else None
    return os.path.join("group_uploads", group_name, file_type, f"{filename}")


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
        upload_to=f"{group_upload_path}/thumbnails", null=True, blank=True
    )
    file_type = models.CharField(max_length=30, null=True, blank=True)
    file_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"in {self.group} - {self.user} says, {self.message}"
