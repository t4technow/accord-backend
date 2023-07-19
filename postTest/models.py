from django.db import models

# Create your models here.

class post(models.Model):
    title = models.CharField("Title", max_length=20)
    