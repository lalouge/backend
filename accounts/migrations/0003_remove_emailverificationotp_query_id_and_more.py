# Generated by Django 4.2.7 on 2024-02-06 12:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_remove_devicetoken_query_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emailverificationotp',
            name='query_id',
        ),
        migrations.RemoveField(
            model_name='otp',
            name='query_id',
        ),
        migrations.RemoveField(
            model_name='phonenumberverificationotp',
            name='query_id',
        ),
        migrations.RemoveField(
            model_name='usedotp',
            name='query_id',
        ),
    ]
