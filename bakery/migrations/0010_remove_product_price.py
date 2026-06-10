from django.db import migrations


class Migration(migrations.Migration):
    """
    ลบ column 'price' ออกจาก DB จริง (bakery_product)
    Django migration state ไม่มี field นี้แล้ว แต่ DB ยังมีอยู่
    ใช้ SeparateDatabaseAndState เพื่อรัน DROP COLUMN โดยไม่แตะ state
    """

    dependencies = [
        ('bakery', '0009_product_image_optional'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE bakery_product DROP COLUMN IF EXISTS price;',
                    reverse_sql='ALTER TABLE bakery_product ADD COLUMN price integer NOT NULL DEFAULT 0;',
                ),
            ],
            state_operations=[],  # state ไม่ต้องเปลี่ยนเพราะ model ลบ field ออกไปแล้ว
        ),
    ]
