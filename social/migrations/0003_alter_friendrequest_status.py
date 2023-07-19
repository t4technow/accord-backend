# Generated by Django 4.2.3 on 2023-07-18 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendrequest',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')], default='pending', max_length=10),
        ),
    ]
