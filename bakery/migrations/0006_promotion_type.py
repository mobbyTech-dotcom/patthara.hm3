from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0005_productsku_promotion'),
    ]

    operations = [
        # ใช้ IF NOT EXISTS กัน error กรณี column มีอยู่แล้วใน DB
        migrations.RunSQL(
            sql="""
                ALTER TABLE bakery_promotion
                    ADD COLUMN IF NOT EXISTS promo_type VARCHAR(20) NOT NULL DEFAULT 'special_price';
                ALTER TABLE bakery_promotion
                    ADD COLUMN IF NOT EXISTS discount INTEGER NULL;
                ALTER TABLE bakery_promotion
                    ALTER COLUMN special_price DROP NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE bakery_promotion DROP COLUMN IF EXISTS promo_type;
                ALTER TABLE bakery_promotion DROP COLUMN IF EXISTS discount;
                ALTER TABLE bakery_promotion ALTER COLUMN special_price SET NOT NULL;
            """,
        ),
        # อัปเดต state ให้ Django รู้จัก field เหล่านี้
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
            ],
            database_operations=[],  # SQL ทำไปแล้วข้างบน
        ),
    ]
