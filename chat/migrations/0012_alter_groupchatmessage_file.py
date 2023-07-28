# Generated by Django 4.2.3 on 2023-07-26 11:15

import chat.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0011_groupchatmessage_file_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupchatmessage',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=chat.models.group_upload_path),
        ),
    ]