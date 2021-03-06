# Generated by Django 2.0.5 on 2018-05-19 23:16

from django.db import migrations


def update_status(apps, schema_editor):
    order_status = apps.get_model("chair", "Order")
    order_status.objects.all().update(has_report=True)


class Migration(migrations.Migration):

    dependencies = [
        ('chair', '0014_order_has_report'),
    ]

    operations = [
        migrations.RunPython(update_status, reverse_code=migrations.RunPython.noop)
    ]
