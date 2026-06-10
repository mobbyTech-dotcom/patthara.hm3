from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0009_product_image_optional'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='price',
        ),
    ]
