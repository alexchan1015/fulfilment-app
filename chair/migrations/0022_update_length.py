from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chair', '0021_customer_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='product_name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
