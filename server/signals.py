from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Server, Channel


@receiver(post_save, sender=Server)
def create_channels(sender, instance, created, **kwargs):
    if created:
        Channel.objects.create(name="general", channel_type="text", server=instance)
        Channel.objects.create(name="general", channel_type="voice", server=instance)

        category = instance.category
        if category == "educational":
            Channel.objects.create(
                name="general", channel_type="video", server=instance
            )
