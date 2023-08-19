from user.models import User
from django.db import models


class Notification(models.Model):
    STATUS_CHOICES = [
        ("unread", "Unread"),
        ("read", "Read"),
    ]

    TYPE_CHOICES = [
        ("message", "Message"),
        ("group_message", "Group Message"),
        ("friend_request", "Friend Request"),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_sender", null=True
    )
    title = models.CharField(max_length=300)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="unread")

    def __str__(self):
        return f"{self.recipient.username} - {self.content}"


class PushNotificationSubscriber(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    device_token = models.CharField(max_length=555)

    def __str__(self):
        return self.user.username
