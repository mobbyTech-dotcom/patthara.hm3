from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0004_order_order_number'),
    ]

    operations = [
        # ลบ field price ออกจาก Product
        migrations.RemoveField(
            model_name='product',
            name='price',
        ),
        # สร้าง ProductSKU
        migrations.CreateModel(
            name='ProductSKU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='ชื่อตัวเลือก (เช่น รสช็อกโกแลต)')),
                ('price', models.PositiveIntegerField(verbose_name='ราคา (บาท)')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='skus',
                    to='bakery.product',
                )),
            ],
            options={
                'verbose_name': 'ตัวเลือกสินค้า (SKU)',
                'verbose_name_plural': 'ตัวเลือกสินค้า (SKUs)',
                'ordering': ['price'],
            },
        ),
        # สร้าง Promotion
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_quantity', models.PositiveIntegerField(verbose_name='ซื้อครบ (ชิ้น)')),
                ('special_price', models.PositiveIntegerField(verbose_name='ราคาพิเศษต่อชิ้น (บาท)')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='promotions',
                    to='bakery.product',
                )),
            ],
            options={
                'verbose_name': 'โปรโมชั่น',
                'verbose_name_plural': 'โปรโมชั่น',
                'ordering': ['-min_quantity'],
            },
        ),
    ]
