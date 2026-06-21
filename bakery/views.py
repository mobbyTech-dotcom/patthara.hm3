from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, F, ExpressionWrapper, IntegerField as IntField
from collections import OrderedDict
from decimal import Decimal

from .models import Product, Order, OrderItem, PaymentInfo, ProductSKU, Promotion, ProductIngredient
from .forms import ProductForm
import json

# ✅ ชื่อที่เก็บใน OrderItem จะเป็น "ชื่อสินค้า (ชื่อ SKU)" เช่น "บราวนี่ (ช็อกโกแลต)"
# ฟังก์ชันนี้ใช้ตัดเอาแค่ชื่อสินค้าจริงๆ กลับมา เพื่อไปหารายการวัตถุดิบ (ProductIngredient) ของสินค้านั้น
def get_base_product_name(display_name):
    return display_name.split(' (')[0].strip()

def get_products_json():
    products = Product.objects.filter(is_available=True).prefetch_related('skus', 'promotions')
    data = {}
    for p in products:
        skus = []
        for sku in p.skus.all():
            skus.append({'id': sku.id, 'name': sku.name, 'price': sku.price, 'image_url': sku.image.url if sku.image else ''})
            
        promos = list(p.promotions.order_by('-min_quantity').values('min_quantity', 'promo_type', 'special_price', 'discount'))
        
        if not skus:
            fallback_price = getattr(p, 'price', getattr(p, 'base_price', 0))
            skus = [{'id': f'p_{p.id}', 'name': 'ปกติ', 'price': fallback_price, 'image_url': ''}]
            
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
    products = Product.objects.all().prefetch_related('ingredients')
    orders   = Order.objects.prefetch_related('items').all()
    form     = ProductForm()
    payment  = PaymentInfo.get_singleton()

    pending_count = Order.objects.filter(status='pending').count()
    confirmed_count = Order.objects.filter(status='confirmed').count()
    active_orders_count = pending_count + confirmed_count

    # ───────────────────────────────────────────────────────────────
    # ✅ สรุปยอดขาย: คิดยอดจาก order.total ของแต่ละออเดอร์ตรงๆ (ค่านี้หักส่วนลดไว้แล้วตั้งแต่ตอนสร้างออเดอร์)
    # แทนการ Sum(price * quantity) ของ OrderItem ตรงๆ ซึ่งไม่ได้หักส่วนลดรวม (โปรแบบ "ส่วนลดรวม บาท")
    # ทำให้ก่อนหน้านี้ยอดรวมในสินค้าที่ขายได้ "เกิน" ยอดขายจริง
    # ส่วนลดของแต่ละออเดอร์จะถูกเฉลี่ยคืนไปตามสัดส่วนราคาในแต่ละ item เพื่อให้ยอดต่อเมนู บวกกันแล้วตรงกับยอดรวมพอดี
    done_orders = Order.objects.filter(status='done').prefetch_related('items')
    done_count  = done_orders.count()
    sales_total = sum(o.total for o in done_orders)

    product_revenue   = OrderedDict()
    done_orders_data  = []
    for o in done_orders:
        items = list(o.items.all())
        raw_sum = sum(it.price * it.quantity for it in items)
        row_items = []
        for it in items:
            raw = it.price * it.quantity
            adjusted = (raw / raw_sum * o.total) if raw_sum > 0 else 0
            row_items.append({'name': it.product_name, 'qty': it.quantity, 'price': it.price})
            entry = product_revenue.setdefault(it.product_name, {'total_qty': 0, 'total_revenue': 0})
            entry['total_qty']     += it.quantity
            entry['total_revenue'] += adjusted
        done_orders_data.append({
            'id': o.id,
            'order_number': o.order_number,
            'customer_name': o.customer_name,
            'total': o.total,
            'items': row_items,
        })

    product_summary_list = sorted(
        [{'product_name': k, 'total_qty': v['total_qty'], 'total_revenue': round(v['total_revenue'])} for k, v in product_revenue.items()],
        key=lambda x: -x['total_qty']
    )

    todo_summary_list = list(
        OrderItem.objects
        .filter(order__status__in=['pending', 'confirmed'])
        .values('product_name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
    )

    # ───────────────────────────────────────────────────────────────
    # ✅ รายการที่ต้องซื้อ: รวมวัตถุดิบ/อุปกรณ์/แพ็คเกจจิ้งจากใบเช็คของแต่ละเมนู (ProductIngredient)
    # คูณด้วยจำนวนที่ต้องทำ (ออเดอร์ที่ยังไม่เสร็จ) แล้วรวมยอดทั้งหมดที่ต้องซื้อ
    shopping_breakdown = []
    shopping_totals     = OrderedDict()
    for item in todo_summary_list:
        base_name  = get_base_product_name(item['product_name'])
        qty_needed = item['total_qty']
        product = Product.objects.filter(name=base_name).prefetch_related('ingredients').first()
        if not product:
            continue
        ing_rows = []
        for ing in product.ingredients.all():
            total_qty = ing.quantity * qty_needed
            ing_rows.append({'name': ing.name, 'unit': ing.unit, 'qty': total_qty})
            key = (ing.name, ing.unit)
            shopping_totals[key] = shopping_totals.get(key, Decimal('0')) + total_qty
        if ing_rows:
            shopping_breakdown.append({
                'product_name': item['product_name'],
                'qty_needed':   qty_needed,
                'ingredients':  ing_rows,
            })
    shopping_list = sorted(
        [{'name': k[0], 'unit': k[1], 'qty': v} for k, v in shopping_totals.items()],
        key=lambda x: x['name']
    )

    return render(request, 'bakery/admin.html', {
        'products':             products,
        'orders':               orders,
        'form':                 form,
        'payment':              payment,
        'pending_count':        pending_count,
        'confirmed_count':      confirmed_count,
        'active_orders_count':  active_orders_count,
        'sales_total':          sales_total,
        'done_count':           done_count,
        'done_orders':          done_orders,
        'done_orders_json':     json.dumps(done_orders_data),
        'product_summary':      product_summary_list,
        'todo_summary':         todo_summary_list,
        'shopping_breakdown':   shopping_breakdown,
        'shopping_list':        shopping_list,
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
            ingredients = json.loads(request.POST.get('ingredients', '[]'))
            
            # ✅ แก้ไขลูปบันทึก SKU ใหม่ให้ดึงรูปตาม index ที่หน้าบ้านส่งมาอย่างถูกต้อง
            for index, item in enumerate(skus):
                orig_idx = item.get('originalIndex', index)
                image_file = request.FILES.get(f'sku_image_{orig_idx}')
                ProductSKU.objects.create(
                    product=product, 
                    name=item['name'], 
                    price=item['price'],
                    image=image_file
                )
                
            for promo in promos:
                Promotion.objects.create(
                    product=product, 
                    min_quantity=promo['min_quantity'], 
                    promo_type=promo.get('promo_type', 'special_price'),
                    special_price=promo.get('special_price') or 0,
                    discount=promo.get('discount') or 0
                )

            # ✅ บันทึกใบเช็ครายการวัตถุดิบ/อุปกรณ์/แพ็คเกจจิ้งของเมนูนี้
            for ing in ingredients:
                ProductIngredient.objects.create(
                    product=product,
                    name=ing['name'],
                    quantity=ing.get('quantity') or 1,
                    unit=ing.get('unit', '')
                )

            return JsonResponse({'success': True})
        except Exception as e:
            print("Error saving SKUs/Promos:", e)
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'errors': form.errors})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            try:
                # --- จัดการ SKU ---
                skus_data = json.loads(request.POST.get('skus', '[]'))
                existing_skus = {str(sku.id): sku for sku in product.skus.all()}
                kept_sku_ids = []
                
                # ✅ แก้ไขการดึงรูปภาพของ SKU ตอนแก้ไขให้ตรงกับหน้าบ้าน
                for index, item in enumerate(skus_data):
                    orig_idx = item.get('originalIndex', index)
                    image_file = request.FILES.get(f'sku_image_{orig_idx}')
                    sku_id = str(item.get('id', ''))
                    
                    if sku_id and sku_id in existing_skus:
                        sku = existing_skus[sku_id]
                        sku.name = item['name']
                        sku.price = item['price']
                        if image_file: 
                            sku.image = image_file
                        sku.save()
                        kept_sku_ids.append(sku.id)
                    else:
                        new_sku = ProductSKU.objects.create(
                            product=product,
                            name=item['name'],
                            price=item['price'],
                            image=image_file
                        )
                        kept_sku_ids.append(new_sku.id)
                
                product.skus.exclude(id__in=kept_sku_ids).delete()
                
                # --- จัดการ Promotion ---
                product.promotions.all().delete()
                promos = json.loads(request.POST.get('promos', '[]'))
                for promo in promos:
                    Promotion.objects.create(
                        product=product, 
                        min_quantity=promo['min_quantity'], 
                        promo_type=promo.get('promo_type', 'special_price'),
                        special_price=promo.get('special_price') or 0,
                        discount=promo.get('discount') or 0
                    )

                # --- จัดการใบเช็ครายการวัตถุดิบ/อุปกรณ์/แพ็คเกจจิ้ง ---
                product.ingredients.all().delete()
                ingredients = json.loads(request.POST.get('ingredients', '[]'))
                for ing in ingredients:
                    ProductIngredient.objects.create(
                        product=product,
                        name=ing['name'],
                        quantity=ing.get('quantity') or 1,
                        unit=ing.get('unit', '')
                    )

                return JsonResponse({'success': True})
            except Exception as e:
                print("Error Edit SKU/Promo:", e)
                return JsonResponse({'success': False, 'error': str(e)})
                
        return JsonResponse({'success': False, 'errors': form.errors})
    
    fallback_price = getattr(product, 'price', getattr(product, 'base_price', 0))
    return JsonResponse({
        'id':          product.id,
        'name':        product.name,
        'price':       fallback_price,
        'description': product.description,
        'image_url':   product.image.url if product.image else '',
        'skus':        [{'id': s.id, 'name': s.name, 'price': s.price, 'image_url': s.image.url if s.image else ''} for s in product.skus.all()],
        'promos':      list(product.promotions.values('min_quantity', 'promo_type', 'special_price', 'discount')),
        'ingredients': list(product.ingredients.values('name', 'quantity', 'unit')),
    })

@login_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    try:
        if product.image: product.image.delete(save=False)
    except Exception: pass
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

# ✅ บันทึกวิธีชำระเงิน (เงินสด/โอนเงิน) ตรงที่ตัวออเดอร์เลย คู่กับช่องสถานะ
@login_required
@require_POST
def order_update_payment_method(request, order_id):
    order  = get_object_or_404(Order, id=order_id)
    method = request.POST.get('payment_method', '')
    if method == '' or method in dict(Order.PAYMENT_METHOD_CHOICES):
        order.payment_method = method
        order.save()
        return JsonResponse({'success': True, 'payment_method': order.payment_method, 'label': order.payment_method_label})
    return JsonResponse({'success': False, 'error': 'invalid payment method'})

@login_required
@require_POST
def order_update_customer(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.customer_name = request.POST.get('customer_name', order.customer_name)
    order.phone = request.POST.get('phone', order.phone)
    order.address = request.POST.get('address', order.address)
    date_str = request.POST.get('appointment_date')
    if date_str:
        order.appointment_date = date_str
    order.note = request.POST.get('note', order.note)
    order.save()
    return JsonResponse({'success': True})

# ✅ ฟังก์ชันใหม่สำหรับ "ยกเลิกออเดอร์" โดยเฉพาะ
@login_required
@require_POST
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    reason = request.POST.get('cancel_reason', '').strip()
    order.status = 'cancelled'
    order.cancel_reason = reason
    order.save()
    return JsonResponse({'success': True})

@login_required
@require_POST
def payment_update(request):
    payment = PaymentInfo.get_singleton()
    payment.bank_name      = request.POST.get('bank_name', '').strip()
    payment.account_number = request.POST.get('account_number', '').strip()
    payment.account_name   = request.POST.get('account_name', '').strip()
    
    qr_file = request.FILES.get('qr_image')
    # ✅ ถ้ามีรูปใหม่ส่งมา ให้นำมาใส่ทับของเดิมไปเลย (ไม่ต้องสั่ง delete ของเดิมให้ระบบ Error)
    if qr_file:
        payment.qr_image = qr_file
        
    payment.save()
    return JsonResponse({'success': True})

@login_required
@require_POST
def payment_delete_qr(request):
    payment = PaymentInfo.get_singleton()
    # ✅ ถอดรูปเก่าออกโดยการเซ็ตเป็น None 
    payment.qr_image = None
    payment.save()
    return JsonResponse({'success': True})
    
@login_required
@require_POST
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    try:
        # ถ้ามีรูปสลิป ให้ลบรูปออกจาก Cloudinary ด้วยเพื่อประหยัดพื้นที่
        if order.slip_image:
            order.slip_image.delete(save=False)
    except Exception:
        pass
    
    order.delete()
    return JsonResponse({'success': True})
    
def handler404(request, exception=None):
    return render(request, 'bakery/404.html', status=404)
