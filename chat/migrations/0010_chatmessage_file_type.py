# Generated by Django 4.2.3 on 2023-07-25 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0009_chatmessage_file_chatmessage_file_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='file_type',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]