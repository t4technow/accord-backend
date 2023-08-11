from user.models import User
from django.db import models


class Server(models.Model):
    SERVER_TYPES = [
        ("gaming", "Gaming"),
        ("educational", "Educational"),
        ("science-and-tech", "Science and Tech"),
        ("entertainment", "Entertainment"),
    ]

    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to="server/avatar", null=True, blank=True)
    cover = models.ImageField(upload_to="server/cover", null=True, blank=True)
    description = models.CharField(max_length=190, null=True, blank=True)
    category = models.CharField(choices=SERVER_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


# class ChannelMAnager(models.Manager):
#     def by_server(self, **kwargs):
#         print(kwargs, "llllllll", self)
#         return self.get_queryset().filter(server=kwargs.get("pk"))


class Channel(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    channel_type = models.CharField(
        max_length=10,
        choices=[
            ("text", "Text"),
            ("voice", "Voice"),
            ("video", "Video"),
            ("file", "File"),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.user.username
