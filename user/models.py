from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.db.models import Q

from social.models import Friend


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def get_friends_with_chat_thread_connections(self, chat_thread_users):
        user_friends = Friend.objects.filter(Q(user=self) | Q(friend=self))
        friends = [
            friend.user if friend.friend == self else friend.friend
            for friend in user_friends
        ]

        # Check if any friend is part of the chat thread
        for friend in friends:
            if friend in chat_thread_users:
                return friends

        # If no friends are part of the chat thread, fetch friends of friends
        friends_of_friends_in_chat_thread = []
        for friend in friends:
            friend_of_friends = Friend.objects.filter(
                Q(user=friend) | Q(friend=friend)
            ).exclude(user=self)
            for friend_of_friend in friend_of_friends:
                if friend_of_friend.user in chat_thread_users:
                    friends_of_friends_in_chat_thread.append(friend_of_friend.user)

        return friends_of_friends_in_chat_thread

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="user/avatar", blank=True, null=True)
    cover = models.ImageField(upload_to="user/cover", blank=True, null=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.email
