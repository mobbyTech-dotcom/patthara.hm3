from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='ชื่อสินค้า')),
                ('price', models.PositiveIntegerField(verbose_name='ราคา (บาท)')),
                ('description', models.TextField(blank=True, verbose_name='รายละเอียด')),
                ('image', models.ImageField(upload_to='products/', verbose_name='รูปภาพ')),
                ('is_available', models.BooleanField(default=True, verbose_name='เปิดขาย')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'สินค้า', 'verbose_name_plural': 'สินค้าทั้งหมด', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=200, verbose_name='ชื่อลูกค้า')),
                ('phone', models.CharField(max_length=20, verbose_name='เบอร์โทร')),
                ('address', models.TextField(verbose_name='ที่อยู่')),
                ('appointment_date', models.DateField(verbose_name='วันนัด')),
                ('note', models.TextField(blank=True, verbose_name='หมายเหตุ')),
                ('total', models.PositiveIntegerField(default=0, verbose_name='ยอดรวม')),
                ('status', models.CharField(choices=[('pending', 'รอดำเนินการ'), ('confirmed', 'ยืนยันแล้ว'), ('done', 'เสร็จสิ้น')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'ออเดอร์', 'verbose_name_plural': 'ออเดอร์ทั้งหมด', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200)),
                ('price', models.PositiveIntegerField()),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='bakery.order')),
            ],
        ),
    ]
