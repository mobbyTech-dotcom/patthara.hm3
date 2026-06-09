from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, F, ExpressionWrapper, IntegerField as IntField

# ⚠️ จุดสำคัญ: ต้องแน่ใจว่ามี ProductSKU และ Promotion อยู่ในบรรทัดนี้ครับ
from .models import Product, Order, OrderItem, PaymentInfo, ProductSKU, Promotion
from .forms import ProductForm
import json

def get_products_json():
    """Helper ดึงข้อมูลสินค้า, SKU และโปรโมชั่น เป็น JSON"""
    products = Product.objects.filter(is_available=True).prefetch_related('skus', 'promotions')
    data = {}
    for p in products:
        skus = list(p.skus.values('id', 'name', 'price'))
        promos = list(p.promotions.order_by('-min_quantity').values('min_quantity', 'promo_type', 'special_price', 'discount'))
        # ถ้าร้านยังไม่ได้ตั้ง SKU ให้ใช้สินค้าหลักเป็น 1 SKU อัตโนมัติ (กันระบบพัง)
        if not skus:
            skus = [{'id': f'p_{p.id}', 'name': 'ปกติ', 'price': 0}]
            
        data[p.id] = {
            'id': p.id,
            'name': p.name,
            'image': p.image.url if p.image else '',
            'skus': skus,
            'promos': promos
        }
    return json.dumps(data)


def index(request):
    products = Product.objects.filter(is_available=True)
    products_json = get_products_json()
    return render(request, 'bakery/index.html', {'products': products, 'products_json': products_json})


def order_page(request):
    products_json = get_products_json()
    return render(request, 'bakery/order.html', {'products_json': products_json})


def create_order(request):
    if request.method == 'POST':
        data  = json.loads(request.body)
        items = data.get('items', [])
        if not items:
            return JsonResponse({'success': False, 'error': 'ไม่มีสินค้า'})
        order = Order.objects.create(
            customer_name    = data['customer_name'],
            phone            = data['phone'],
            address          = data['address'],
            appointment_date = data['appointment_date'],
            note             = data.get('note', ''),
            total            = data['total'],
        )
        for item in items:
            OrderItem.objects.create(
                order        = order,
                product_name = item['name'],
                price        = item['price'],
                quantity     = item['quantity'],
            )
        return JsonResponse({'success': True, 'order_id': order.order_number})
    return JsonResponse({'success': False})


def order_receipt(request, order_number):
    order   = get_object_or_404(Order, order_number=order_number)
    payment = PaymentInfo.get_singleton()
    return render(request, 'bakery/receipt.html', {'order': order, 'payment': payment})


def upload_slip(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        slip = request.FILES.get('slip_image')
        if slip:
            order.slip_image = slip
            order.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'ไม่พบไฟล์'})
    return JsonResponse({'success': False})


def track_order(request):
    order = None
    error = None
    if request.method == 'POST':
        order_id = request.POST.get('order_id', '').strip()
        if order_id:
            try:
                order = Order.objects.prefetch_related('items').get(order_number=order_id)
            except Order.DoesNotExist:
                error = f'ไม่พบออเดอร์หมายเลข {order_id}'
        else:
            error = 'กรุณากรอกหมายเลขออเดอร์'
    return render(request, 'bakery/track.html', {'order': order, 'error': error})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_panel')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'
        elif not user.is_staff:
            error = 'บัญชีนี้ยังไม่มีสิทธิ์เข้าหลังบ้าน กรุณาติดต่อแอดมิน'
        else:
            login(request, user)
            return redirect('admin_panel')
    return render(request, 'bakery/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def admin_panel(request):
    products = Product.objects.prefetch_related('skus', 'promotions').all()
    orders   = Order.objects.prefetch_related('items').all()
    form     = ProductForm()
    payment  = PaymentInfo.get_singleton()

    active_orders_count = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    done_orders = Order.objects.filter(status='done')
    sales_total = done_orders.aggregate(total=Sum('total'))['total'] or 0
    done_count  = done_orders.count()

    product_summary_list = list(
        OrderItem.objects
        .filter(order__status='done')
        .values('product_name')
        .annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(
                ExpressionWrapper(
                    F('price') * F('quantity'),
                    output_field=IntField()
                )
            )
        )
        .order_by('-total_qty')
    )

    return render(request, 'bakery/admin.html', {
        'products':             products,
        'orders':               orders,
        'form':                 form,
        'payment':              payment,
        'active_orders_count':  active_orders_count,
        'sales_total':          sales_total,
        'done_count':           done_count,
        'product_summary':      product_summary_list,
    })


@login_required
@require_POST
def product_add(request):
    form = ProductForm(request.POST, request.FILES)
    if form.is_valid():
        product = form.save()
        
        try:
            skus = json.loads(request.POST.get('skus', '[]'))
            promos = json.loads(request.POST.get('promos', '[]'))
            
            for sku in skus:
                ProductSKU.objects.create(product=product, name=sku['name'], price=sku['price'])
            for promo in promos:
                ptype = promo.get('promo_type', 'special_price')
                Promotion.objects.create(
                    product=product,
                    min_quantity=promo['min_quantity'],
                    promo_type=ptype,
                    special_price=promo.get('special_price') or None,
                    discount=promo.get('discount') or None,
                )
        except Exception as e:
            print("Error saving SKUs/Promos:", e)
            pass
            
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': form.errors})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            
            try:
                # ลบ SKU และ Promotion เดิมทิ้งก่อนสร้างใหม่
                product.skus.all().delete()
                product.promotions.all().delete()
                
                skus = json.loads(request.POST.get('skus', '[]'))
                promos = json.loads(request.POST.get('promos', '[]'))
                
                for sku in skus:
                    ProductSKU.objects.create(product=product, name=sku['name'], price=sku['price'])
                for promo in promos:
                    ptype = promo.get('promo_type', 'special_price')
                    Promotion.objects.create(
                        product=product,
                        min_quantity=promo['min_quantity'],
                        promo_type=ptype,
                        special_price=promo.get('special_price') or None,
                        discount=promo.get('discount') or None,
                    )
            except Exception as e:
                # ปริ้นท์ Error เผื่อไว้ดูในหน้า Logs ของ Render
                print("Error Edit SKU/Promo:", e)
                pass

            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({
        'id':          product.id,
        'name':        product.name,
        
        'description': product.description,
        'image_url':   product.image.url if product.image else '',
        'skus':        list(product.skus.values('name', 'price')),
        'promos':      list(product.promotions.values('min_quantity', 'promo_type', 'special_price', 'discount')),
    })


@login_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        if product.image:
            product.image.delete(save=False)
    except Exception:
        pass
    product.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_available = not product.is_available
    product.save()
    return JsonResponse({'success': True, 'is_available': product.is_available})


@login_required
@require_POST
def order_update_status(request, order_id):
    order  = get_object_or_404(Order, id=order_id)
    status = request.POST.get('status')
    if status in dict(Order.STATUS_CHOICES):
        order.status = status
        order.save()
        return JsonResponse({'success': True, 'status': status, 'label': order.status_label})
    return JsonResponse({'success': False, 'error': 'invalid status'})


@login_required
@require_POST
def payment_update(request):
    payment = PaymentInfo.get_singleton()
    payment.bank_name      = request.POST.get('bank_name', '').strip()
    payment.account_number = request.POST.get('account_number', '').strip()
    payment.account_name   = request.POST.get('account_name', '').strip()
    qr_file = request.FILES.get('qr_image')
    if qr_file:
        if payment.qr_image:
            payment.qr_image.delete(save=False)
        payment.qr_image = qr_file
    payment.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def payment_delete_qr(request):
    payment = PaymentInfo.get_singleton()
    if payment.qr_image:
        payment.qr_image.delete(save=False)
        payment.qr_image = None
        payment.save()
    return JsonResponse({'success': True})


def handler404(request, exception=None):
    return render(request, 'bakery/404.html', status=404)
