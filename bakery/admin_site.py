from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductSKU, Promotion, ProductIngredient, Order, OrderItem, PaymentInfo

class ProductSKUInline(admin.TabularInline):
    model = ProductSKU
    extra = 1
    fields = ('name', 'price', 'image', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px; border-radius:4px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = "พรีวิวรูปภาพ"

class PromotionInline(admin.TabularInline):
    model = Promotion
    extra = 1

class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_available', 'created_at')
    inlines = [ProductSKUInline, PromotionInline, ProductIngredientInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity', 'subtotal')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'phone', 'total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]

@admin.register(PaymentInfo)
class PaymentInfoAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_number', 'account_name', 'updated_at')
