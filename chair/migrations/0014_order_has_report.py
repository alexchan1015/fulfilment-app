# Generated by Django 2.0.5 on 2018-06-01 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chair', '0013_order_bestbuy_filled'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='has_report',
            field=models.BooleanField(default=False),
        ),
    ]
