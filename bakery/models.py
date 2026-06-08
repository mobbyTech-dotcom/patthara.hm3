from django.db import models
from cloudinary.models import CloudinaryField
import random
import string

def generate_order_number():
    """สร้างเลขออเดอร์สุ่ม 8 หลัก เช่น PT-A3X9K2MQ"""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=8))
    return f'PT-{suffix}'

class Product(models.Model):
    name        = models.CharField(max_length=200, verbose_name='ชื่อสินค้า')
    price       = models.PositiveIntegerField(verbose_name='ราคาเริ่มต้น (บาท)')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    image       = CloudinaryField('image', folder='patthara/products')
    is_available = models.BooleanField(default=True, verbose_name='เปิดขาย')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'สินค้า'
        verbose_name_plural = 'สินค้าทั้งหมด'
        ordering            = ['-created_at']

    def __str__(self):
        return self.name

class ProductSKU(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='skus')
    name    = models.CharField(max_length=100, verbose_name='ชื่อตัวเลือก (เช่น รสช็อกโกแลต)')
    price   = models.PositiveIntegerField(verbose_name='ราคา (บาท)')

    class Meta:
        verbose_name        = 'ตัวเลือกสินค้า (SKU)'
        verbose_name_plural = 'ตัวเลือกสินค้า (SKUs)'

    def __str__(self):
        return f"{self.product.name} - {self.name}"

class Promotion(models.Model):
    product       = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='promotions')
    min_quantity  = models.PositiveIntegerField(verbose_name='ซื้อครบ (ชิ้น)')
    special_price = models.PositiveIntegerField(verbose_name='ราคาพิเศษต่อชิ้น (บาท)')

    class Meta:
        verbose_name        = 'โปรโมชั่น'
        verbose_name_plural = 'โปรโมชั่น'
        ordering            = ['-min_quantity']

    def __str__(self):
        return f"ซื้อ {self.min_quantity} ชิ้น เหลือชิ้นละ {self.special_price} บาท"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'รอดำเนินการ'),
        ('confirmed', 'ยืนยันแล้ว'),
        ('done',      'เสร็จสิ้น'),
    ]
    order_number     = models.CharField(max_length=20, unique=True, default=generate_order_number, verbose_name='เลขออเดอร์')
    customer_name    = models.CharField(max_length=200, verbose_name='ชื่อลูกค้า')
    phone            = models.CharField(max_length=20,  verbose_name='เบอร์โทร')
    address          = models.TextField(verbose_name='ที่อยู่')
    appointment_date = models.DateField(verbose_name='วันนัด')
    note             = models.TextField(blank=True, verbose_name='หมายเหตุ')
    total            = models.PositiveIntegerField(default=0, verbose_name='ยอดรวม')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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
        }.get(self.status, 'bg-gray-100 text-gray-500')

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
