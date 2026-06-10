from django.db import migrations
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0008_order_cancel_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image',
            field=cloudinary.models.CloudinaryField(
                'image',
                blank=True,
                max_length=255,
                null=True,
                folder='patthara/products',
            ),
        ),
    ]
