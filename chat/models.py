from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class Group(models.Model):
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to="avatar/group", null=True, blank=True)
    members = models.ManyToManyField(User, through="GroupMembership")


class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)


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


class ChatMessage(models.Model):
    thread = models.ForeignKey(
        ChatThread,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="chat_message_thread",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"in {self.thread} - {self.user} says, {self.message}"
