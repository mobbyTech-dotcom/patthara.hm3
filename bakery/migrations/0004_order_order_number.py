from django.db import migrations, models
import bakery.models


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0003_cloudinary_and_slip'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(
                default=bakery.models.generate_order_number,
                max_length=20,
                unique=True,
                verbose_name='เลขออเดอร์'
            ),
        ),
    ]
