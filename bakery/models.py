from django.db import models
from cloudinary.models import CloudinaryField
import random
import string

def generate_order_number():
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=8))
    return f'PT-{suffix}'

class Product(models.Model):
    name         = models.CharField(max_length=200, verbose_name='ชื่อสินค้า')
    description  = models.TextField(blank=True, verbose_name='รายละเอียด')
    image        = CloudinaryField('image', folder='patthara/products', blank=True, null=True)
    is_available = models.BooleanField(default=True, verbose_name='เปิดขาย')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'สินค้า'
        verbose_name_plural = 'สินค้าทั้งหมด'
        ordering            = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def base_price(self):
        sku = self.skus.order_by('price').first()
        return sku.price if sku else 0

class ProductSKU(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='skus')
    name    = models.CharField(max_length=100, verbose_name='ชื่อตัวเลือก (เช่น รสช็อกโกแลต)')
    price   = models.PositiveIntegerField(verbose_name='ราคา (บาท)')
    image   = CloudinaryField('image', folder='patthara/skus', blank=True, null=True)

    class Meta:
        verbose_name        = 'ตัวเลือกสินค้า (SKU)'
        verbose_name_plural = 'ตัวเลือกสินค้า (SKUs)'
        ordering            = ['price']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

# ✅ ใบเช็ครายการวัตถุดิบ/อุปกรณ์/แพ็คเกจจิ้ง ต่อเมนู (ต่อ 1 ชิ้น)
# ใช้สรุปยอดรวมว่าต้องซื้ออะไรบ้าง เท่าไหร่ ก่อนเตรียมของจริง
class ProductIngredient(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ingredients')
    name     = models.CharField(max_length=200, verbose_name='ชื่อวัตถุดิบ/อุปกรณ์/แพ็คเกจจิ้ง')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name='ปริมาณต่อ 1 ชิ้น')
    unit     = models.CharField(max_length=50, blank=True, default='', verbose_name='หน่วย (เช่น กรัม, ฟอง, ถุง, ชิ้น)')

    class Meta:
        verbose_name        = 'วัตถุดิบของเมนู'
        verbose_name_plural = 'รายการวัตถุดิบของเมนู'
        ordering            = ['id']

    def __str__(self):
        unit = f' {self.unit}' if self.unit else ''
        return f'{self.product.name} – {self.name} x{self.quantity}{unit}'

class Promotion(models.Model):
    TYPE_SPECIAL_PRICE = 'special_price'
    TYPE_DISCOUNT      = 'discount'
    TYPE_CHOICES = [
        (TYPE_SPECIAL_PRICE, 'ราคาพิเศษต่อชิ้น'),
        (TYPE_DISCOUNT,      'ส่วนลดรวม (บาท)'),
    ]

    product       = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='promotions')
    min_quantity  = models.PositiveIntegerField(verbose_name='ซื้อครบ (ชิ้น)')
    promo_type    = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SPECIAL_PRICE, verbose_name='ประเภทโปร')
    special_price = models.PositiveIntegerField(null=True, blank=True, verbose_name='ราคาพิเศษต่อชิ้น (บาท)')
    discount      = models.PositiveIntegerField(null=True, blank=True, verbose_name='ส่วนลดรวม (บาท)')

    class Meta:
        verbose_name        = 'โปรโมชั่น'
        verbose_name_plural = 'โปรโมชั่น'
        ordering            = ['-min_quantity']

    def __str__(self):
        if self.promo_type == self.TYPE_SPECIAL_PRICE:
            return f"ซื้อ {self.min_quantity} ชิ้น เหลือชิ้นละ {self.special_price} บาท"
        return f"ซื้อ {self.min_quantity} ชิ้น ลด {self.discount} บาท"

class Order(models.Model):
    # ✅ เพิ่มสถานะยกเลิก
    STATUS_CHOICES = [
        ('pending',   'รอดำเนินการ'),
        ('confirmed', 'ยืนยันแล้ว'),
        ('done',      'เสร็จสิ้น'),
        ('cancelled', 'ยกเลิกแล้ว'), 
    ]
    # ✅ เพิ่มวิธีชำระเงิน (เงินสด / โอนเงิน) ให้แอดมินเลือกตรงที่ตัวออเดอร์
    PAYMENT_METHOD_CHOICES = [
        ('cash',     'เงินสด'),
        ('transfer', 'โอนเงิน'),
    ]
    order_number     = models.CharField(max_length=20, unique=True, default=generate_order_number, verbose_name='เลขออเดอร์')
    customer_name    = models.CharField(max_length=200, verbose_name='ชื่อลูกค้า')
    phone            = models.CharField(max_length=20,  verbose_name='เบอร์โทร')
    address          = models.TextField(verbose_name='ที่อยู่')
    appointment_date = models.DateField(verbose_name='วันนัด')
    note             = models.TextField(blank=True, verbose_name='หมายเหตุ')
    total            = models.PositiveIntegerField(default=0, verbose_name='ยอดรวม')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # ✅ เพิ่มช่องเก็บเหตุผลการยกเลิก
    cancel_reason    = models.TextField(blank=True, null=True, verbose_name='เหตุผลที่ยกเลิก')
    payment_method   = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, default='', verbose_name='วิธีชำระเงิน')
    slip_image       = CloudinaryField('image', folder='patthara/slips', blank=True, null=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'ออเดอร์'
        verbose_name_plural = 'ออเดอร์ทั้งหมด'
        ordering            = ['-created_at']

    def __str__(self):
        return f'ออเดอร์ {self.order_number} - {self.customer_name}'

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def status_color(self):
        return {
            'pending':   'bg-yellow-100 text-yellow-700',
            'confirmed': 'bg-blue-100 text-blue-700',
            'done':      'bg-green-100 text-green-700',
            'cancelled': 'bg-red-100 text-red-700',
        }.get(self.status, 'bg-gray-100 text-gray-500')

    @property
    def payment_method_label(self):
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, 'ยังไม่ระบุ')

class OrderItem(models.Model):
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    price        = models.PositiveIntegerField()
    quantity     = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

class PaymentInfo(models.Model):
    bank_name      = models.CharField(max_length=100, verbose_name='ชื่อธนาคาร', blank=True)
    account_number = models.CharField(max_length=50,  verbose_name='เลขที่บัญชี', blank=True)
    account_name   = models.CharField(max_length=200, verbose_name='ชื่อบัญชี',   blank=True)
    qr_image       = CloudinaryField('image', folder='patthara/payment', blank=True, null=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'ข้อมูลการชำระเงิน'
        verbose_name_plural = 'ข้อมูลการชำระเงิน'

    def __str__(self):
        return f'การชำระเงิน — {self.bank_name} {self.account_number}'

    @classmethod
    def get_singleton(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
