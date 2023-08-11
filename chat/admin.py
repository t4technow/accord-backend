from django.contrib import admin
from .models import (
    ChatThread,
    ChatMessage,
    CallLog,
    Group,
    GroupMembership,
    GroupChatMessage,
    GroupMessageDeliveryInfo,
    ChannelMessage,
    GroupMessageReadInfo,
)

# Register your models here.

admin.site.register(ChatMessage)
admin.site.register(ChatThread)

admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(GroupChatMessage)
admin.site.register(GroupMessageDeliveryInfo)
admin.site.register(ChannelMessage)

admin.site.register(GroupMessageReadInfo)
admin.site.register(CallLog)
