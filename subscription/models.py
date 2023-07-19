from user.models import User
from django.db import models


class Subscription(models.Model):
    SUBSCRIPTION_TYPES = [
        ("server", "Server"),
        ("nos", "NOS"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPES)
    is_lifetime = models.BooleanField(default=False)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
