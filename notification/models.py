from user.models import User
from django.db import models


class Notification(models.Model):
    STATUS_CHOICES = [
        ("unread", "Unread"),
        ("read", "Read"),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="unread")

    def __str__(self):
        return f"{self.recipient.username} - {self.content}"
