from django.db import migrations
import cloudinary.models


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0002_paymentinfo'),
    ]

    operations = [
        # Product.image → CloudinaryField
        migrations.AlterField(
            model_name='product',
            name='image',
            field=cloudinary.models.CloudinaryField('image', max_length=255),
        ),
        # PaymentInfo.qr_image → CloudinaryField
        migrations.AlterField(
            model_name='paymentinfo',
            name='qr_image',
            field=cloudinary.models.CloudinaryField('image', blank=True, max_length=255, null=True),
        ),
        # Order.slip_image → CloudinaryField (ใหม่)
        migrations.AddField(
            model_name='order',
            name='slip_image',
            field=cloudinary.models.CloudinaryField('image', blank=True, max_length=255, null=True),
        ),
    ]
