from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0010_remove_product_price'),
    ]

    operations = [
        # ✅ ใบเช็ครายการวัตถุดิบ/อุปกรณ์/แพ็คเกจจิ้งต่อเมนู
        migrations.CreateModel(
            name='ProductIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='ชื่อวัตถุดิบ/อุปกรณ์/แพ็คเกจจิ้ง')),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='ปริมาณต่อ 1 ชิ้น')),
                ('unit', models.CharField(blank=True, default='', max_length=50, verbose_name='หน่วย (เช่น กรัม, ฟอง, ถุง, ชิ้น)')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients', to='bakery.product')),
            ],
            options={
                'verbose_name': 'วัตถุดิบของเมนู',
                'verbose_name_plural': 'รายการวัตถุดิบของเมนู',
                'ordering': ['id'],
            },
        ),
        # ✅ วิธีชำระเงิน (เงินสด / โอนเงิน) ต่อออเดอร์
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(blank=True, choices=[('cash', 'เงินสด'), ('transfer', 'โอนเงิน')], default='', max_length=20, verbose_name='วิธีชำระเงิน'),
        ),
    ]
