from user.models import User, UserProfile
from django.db import models
from django.db.models import Q


class Friend(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends")
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friend_of")
    established_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "friend"]

    def __str__(self):
        return self.user.username


class FriendRequest(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_friend_requests"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_friend_requests"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS,
        default="pending",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sender
