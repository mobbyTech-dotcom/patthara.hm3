from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(max_length=100, verbose_name='ชื่อธนาคาร', blank=True)),
                ('account_number', models.CharField(max_length=50, verbose_name='เลขที่บัญชี', blank=True)),
                ('account_name', models.CharField(max_length=200, verbose_name='ชื่อบัญชี', blank=True)),
                ('qr_image', models.ImageField(upload_to='payment/', verbose_name='QR Code', blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'ข้อมูลการชำระเงิน',
                'verbose_name_plural': 'ข้อมูลการชำระเงิน',
            },
        ),
    ]
