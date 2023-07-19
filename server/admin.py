from django.contrib import admin
from .models import Server, Channel

# Register your models here.

admin.site.register(Server)

class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'channel_type')

admin.site.register(Channel, ChannelAdmin)
