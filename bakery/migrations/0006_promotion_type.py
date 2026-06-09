from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0005_productsku_promotion'),
    ]

    operations = [
        migrations.AddField(
            model_name='promotion',
            name='promo_type',
            field=models.CharField(
                max_length=20,
                choices=[('special_price', 'ราคาพิเศษต่อชิ้น'), ('discount', 'ส่วนลดรวม (บาท)')],
                default='special_price',
                verbose_name='ประเภทโปร',
            ),
        ),
        migrations.AlterField(
            model_name='promotion',
            name='special_price',
            field=models.PositiveIntegerField(null=True, blank=True, verbose_name='ราคาพิเศษต่อชิ้น (บาท)'),
        ),
        migrations.AddField(
            model_name='promotion',
            name='discount',
            field=models.PositiveIntegerField(null=True, blank=True, verbose_name='ส่วนลดรวม (บาท)'),
        ),
    ]
