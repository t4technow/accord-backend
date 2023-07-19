from django.contrib import admin
from .models import Friend, FriendRequest


class FriendAdmin(admin.ModelAdmin):
    list_display = ("user", "friend")


admin.site.register(Friend, FriendAdmin)


class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver")


admin.site.register(FriendRequest, FriendRequestAdmin)
