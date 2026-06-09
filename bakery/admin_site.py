from django.contrib import admin
from .models import Product, ProductSKU, Promotion


class ProductSKUInline(admin.TabularInline):
    model  = ProductSKU
    extra  = 1
    fields = ['name', 'price']


class PromotionInline(admin.TabularInline):
    model  = Promotion
    extra  = 0
    fields = ['min_quantity', 'special_price']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'is_available', 'created_at']   # ลบ 'price' ออก เพราะย้ายไป SKU แล้ว
    list_editable = ['is_available']
    inlines       = [ProductSKUInline, PromotionInline]
