from django.contrib import admin
from user.models import User, UserProfile

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username')

admin.site.register(User, UserAdmin)

admin.site.register(UserProfile)