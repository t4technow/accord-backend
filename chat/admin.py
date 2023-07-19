from django.contrib import admin
from .models import ChatThread, ChatMessage

# Register your models here.

admin.site.register(ChatMessage)
admin.site.register(ChatThread)