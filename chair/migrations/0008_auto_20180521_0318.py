# Generated by Django 2.0.5 on 2018-05-21 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chair', '0007_create_order_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
