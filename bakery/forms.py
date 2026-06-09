from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # เอา 'price' ออกจาก fields เพราะเราย้ายไปตั้งราคาใน SKU แล้วครับ
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl px-3.5 py-2 text-sm focus:ring-2 focus:ring-blue-400',
                'placeholder': 'ชื่อสินค้า'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-xl px-3.5 py-2 text-sm focus:ring-2 focus:ring-blue-400',
                'rows': '3'
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
                'id': 'prod-img-file',
                'onchange': 'previewImage(event)'
            }),
        }
