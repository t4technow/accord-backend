from django.contrib import admin
from .models import ChatThread, ChatMessage, Group, GroupMembership, GroupChatMessage

# Register your models here.

admin.site.register(ChatMessage)
admin.site.register(ChatThread)

admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(GroupChatMessage)
