from django.contrib import admin
from .models import Notification, PushNotificationSubscriber


admin.site.register(Notification)
admin.site.register(PushNotificationSubscriber)
