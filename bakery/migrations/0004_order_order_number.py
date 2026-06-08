from django.db import migrations, models
import bakery.models
import random
import string


def set_unique_order_numbers(apps, schema_editor):
    Order = apps.get_model('bakery', 'Order')
    used = set()
    for order in Order.objects.all():
        while True:
            chars = string.ascii_uppercase + string.digits
            num = 'PT-' + ''.join(random.choices(chars, k=8))
            if num not in used:
                used.add(num)
                order.order_number = num
                order.save(update_fields=['order_number'])
                break


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0003_cloudinary_and_slip'),
    ]

    operations = [
        # เพิ่ม field ก่อนโดยไม่ unique และมี default ชั่วคราว
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(max_length=20, default='PT-TEMP', verbose_name='เลขออเดอร์'),
        ),
        # กำหนดค่า unique ให้แต่ละ row
        migrations.RunPython(set_unique_order_numbers, migrations.RunPython.noop),
        # แล้วค่อย set unique=True
        migrations.AlterField(
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
