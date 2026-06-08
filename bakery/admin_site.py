from django.contrib import admin
from .models import Product, ProductSKU, Promotion

class ProductSKUInline(admin.TabularInline):
    model = ProductSKU
    extra = 1

class PromotionInline(admin.TabularInline):
    model = Promotion
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_available', 'created_at']
    list_editable = ['is_available']
    inlines = [ProductSKUInline, PromotionInline]
