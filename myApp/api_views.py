"""
Alpha Mart — REST API Views
All endpoints return JSON. Consumed by the HTML/JS frontend.

NEW FILE — place at:  myApp/api_views.py

Endpoints:
  GET  /api/products/               — list products (filters: ?q= ?cat= ?condition= ?sort= ?min_price= ?max_price=)
  GET  /api/products/<id>/          — single product with images + related
  GET  /api/categories/             — all categories

  POST /api/auth/register/          — create account
  POST /api/auth/login/             — login, returns user info
  POST /api/auth/logout/            — logout

  GET  /api/cart/                   — view cart items
  POST /api/cart/add/<id>/          — add product to cart
  POST /api/cart/remove/<id>/       — remove product from cart

  POST /api/payment/esewa/initiate/ — start eSewa payment → returns form data to post to eSewa
  GET  /api/payment/esewa/verify/   — eSewa callback after payment (called by eSewa automatically)
  POST /api/payment/khalti/initiate/— start Khalti payment → returns redirect URL
  POST /api/payment/khalti/verify/  — verify Khalti after redirect (called by frontend with pidx)
  POST /api/payment/card/process/   — simulated card payment (demo only)
  POST /api/payment/cod/place/      — place COD order (Kathmandu Valley only)

  GET  /api/orders/                 — list current user's orders
"""

import json
import uuid
import hmac
import hashlib
import base64
import urllib.request as urllib_req
from datetime        import datetime, timezone

from django.http                    import JsonResponse
from django.views.decorators.csrf   import csrf_exempt
from django.views.decorators.http   import require_http_methods
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.models     import User
from django.db.models               import Q
from django.conf                    import settings

from .models import Product, Category, Cart, Order, UserProfile


# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────

def json_ok(data):
    """Return a 200 JSON response."""
    return JsonResponse(data, safe=isinstance(data, dict))

def json_error(msg, status=400):
    """Return an error JSON response."""
    return JsonResponse({'success': False, 'error': msg}, status=status)

def json_success(data=None, msg='Success'):
    """Return a success JSON response."""
    payload = {'success': True, 'message': msg}
    if data:
        payload.update(data)
    return JsonResponse(payload)

def product_to_dict(p, request=None):
    """Serialize a Product object into a dict for the frontend."""
    # Get main image URL
    main_image = None
    first_img  = p.images.first()
    if first_img:
        main_image = request.build_absolute_uri(first_img.image.url) if request else first_img.image.url

    # Map category slug to emoji icon used by frontend
    icon_map = {'phones': '📱', 'laptops': '💻', 'cameras': '📷'}
    cat_slug = p.category.slug if p.category else ''

    return {
        'id':            p.pk,
        'name':          p.title,
        'title':         p.title,
        'description':   p.description,
        'price':         float(p.price),
        'condition':     p.condition,
        'status':        p.status,
        'category':      p.category.name if p.category else '',
        'category_slug': cat_slug,
        'icon':          icon_map.get(cat_slug, '📦'),
        'location':      p.location,
        'image':         main_image,
        'created_at':    p.created_at.isoformat(),
    }

def make_ref_id():
    """Generate a unique internal payment reference ID e.g. AM-3F9A1C2B4E"""
    return 'AM-' + uuid.uuid4().hex[:10].upper()


# ─────────────────────────────────────────────────────────────────
#  PRODUCTS
# ─────────────────────────────────────────────────────────────────

def api_products(request):
    """GET /api/products/"""
    qs = Product.objects.filter(status='available') \
                        .select_related('category') \
                        .prefetch_related('images') \
                        .order_by('-created_at')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # Category by slug  e.g. ?cat=phones
    cat = request.GET.get('cat', '').strip()
    if cat:
        qs = qs.filter(category__slug=cat)

    # Condition  e.g. ?condition=excellent
    cond = request.GET.get('condition', '').strip()
    if cond:
        qs = qs.filter(condition=cond)

    # Price range
    try:
        if request.GET.get('min_price'):
            qs = qs.filter(price__gte=float(request.GET['min_price']))
        if request.GET.get('max_price'):
            qs = qs.filter(price__lte=float(request.GET['max_price']))
    except ValueError:
        pass

    # Sort
    sort_map = {
        'newest':     '-created_at',
        'oldest':     'created_at',
        'price_low':  'price',
        'price_high': '-price',
    }
    sort = request.GET.get('sort', 'newest')
    qs   = qs.order_by(sort_map.get(sort, '-created_at'))

    data = [product_to_dict(p, request) for p in qs]
    return json_ok({'products': data, 'count': len(data)})


def api_product_detail(request, pk):
    """GET /api/products/<pk>/"""
    try:
        p = Product.objects.select_related('category', 'seller') \
                           .prefetch_related('images') \
                           .get(pk=pk)
    except Product.DoesNotExist:
        return json_error('Product not found', 404)

    # All images
    images = [
        {
            'url':     request.build_absolute_uri(img.image.url) if request else img.image.url,
            'is_main': img.is_main,
        }
        for img in p.images.all()
    ]

    # Related products (same category)
    related = Product.objects.filter(category=p.category, status='available') \
                             .exclude(pk=pk) \
                             .prefetch_related('images')[:4]

    d = product_to_dict(p, request)
    d['images']  = images
    d['related'] = [product_to_dict(r, request) for r in related]
    return json_ok(d)


def api_categories(request):
    """GET /api/categories/"""
    cats = Category.objects.all()
    data = [{'id': c.pk, 'name': c.name, 'slug': c.slug, 'icon': c.icon} for c in cats]
    return json_ok({'categories': data})


# ─────────────────────────────────────────────────────────────────
#  AUTHENTICATION
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def api_register(request):
    """POST /api/auth/register/"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('Invalid JSON body')

    first_name = body.get('first_name', '').strip()
    last_name  = body.get('last_name', '').strip()
    email      = body.get('email', '').strip().lower()
    phone      = body.get('phone', '').strip()
    password   = body.get('password', '')

    if not all([first_name, last_name, email, password]):
        return json_error('first_name, last_name, email and password are all required')

    if len(password) < 8:
        return json_error('Password must be at least 8 characters')

    if User.objects.filter(email=email).exists():
        return json_error('An account with this email already exists')

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    UserProfile.objects.create(user=user, phone=phone)
    login(request, user)

    return json_success({
        'user': {
            'id':        user.pk,
            'firstName': user.first_name,
            'lastName':  user.last_name,
            'fullName':  f"{user.first_name} {user.last_name}",
            'email':     user.email,
            'phone':     phone,
        }
    }, 'Account created successfully')


@csrf_exempt
@require_http_methods(['POST'])
def api_login(request):
    """POST /api/auth/login/"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('Invalid JSON body')

    email    = body.get('email', '').strip().lower()
    password = body.get('password', '')

    user = authenticate(request, username=email, password=password)
    if user is None:
        return json_error('Invalid email or password', 401)

    login(request, user)
    profile = getattr(user, 'userprofile', None)

    return json_success({
        'user': {
            'id':        user.pk,
            'firstName': user.first_name,
            'lastName':  user.last_name,
            'fullName':  f"{user.first_name} {user.last_name}",
            'email':     user.email,
            'phone':     profile.phone if profile else '',
        }
    }, f'Welcome back, {user.first_name}!')


@csrf_exempt
@require_http_methods(['POST'])
def api_logout(request):
    """POST /api/auth/logout/"""
    logout(request)
    return json_success(msg='Logged out successfully')


# ─────────────────────────────────────────────────────────────────
#  CART
# ─────────────────────────────────────────────────────────────────

def api_cart(request):
    """GET /api/cart/"""
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    items = Cart.objects.filter(user=request.user).select_related('product', 'product__category')
    data  = []
    total = 0
    for item in items:
        p = item.product
        data.append({
            'cart_id':    item.pk,
            'product_id': p.pk,
            'name':       p.title,
            'price':      float(p.price),
            'condition':  p.condition,
            'category':   p.category.name if p.category else '',
        })
        total += float(p.price)

    return json_ok({'items': data, 'total': total, 'count': len(data)})


@csrf_exempt
@require_http_methods(['POST'])
def api_cart_add(request, pk):
    """POST /api/cart/add/<pk>/"""
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    product = Product.objects.filter(pk=pk, status='available').first()
    if not product:
        return json_error('Product not found or no longer available', 404)

    if product.seller == request.user:
        return json_error("You cannot add your own product to cart")

    Cart.objects.get_or_create(user=request.user, product=product)
    return json_success(msg=f'"{product.title}" added to cart')


@csrf_exempt
@require_http_methods(['POST'])
def api_cart_remove(request, pk):
    """POST /api/cart/remove/<pk>/"""
    if not request.user.is_authenticated:
        return json_error('Login required', 401)
    Cart.objects.filter(user=request.user, product_id=pk).delete()
    return json_success(msg='Item removed from cart')


# ─────────────────────────────────────────────────────────────────
#  PAYMENT HELPERS
# ─────────────────────────────────────────────────────────────────

def _get_cart_products(request, product_ids):
    """Validate and return product queryset from given IDs."""
    products = Product.objects.filter(pk__in=product_ids, status='available')
    if not products.exists():
        return None, json_error('No valid available products found')
    return products, None

def _create_orders(user, products, shipping_amount, discount_amount,
                   total, ref_id, payment_method, payment_status,
                   shipping_address, buyer_name, buyer_phone):
    """Create one Order row per product and return the list."""
    count  = len(products)
    orders = []
    for p in products:
        order = Order.objects.create(
            buyer=user,
            product=p,
            amount=float(p.price),
            shipping_amount=round(shipping_amount / count, 2),
            discount_amount=round(discount_amount / count, 2),
            total_amount=round(total / count, 2),
            status='pending',
            payment_method=payment_method,
            payment_status=payment_status,
            payment_ref_id=ref_id,
            shipping_address=shipping_address,
            buyer_name=buyer_name,
            buyer_phone=buyer_phone,
        )
        orders.append(order)
    return orders


# ─────────────────────────────────────────────────────────────────
#  PAYMENT — eSewa
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def api_esewa_initiate(request):
    """
    POST /api/payment/esewa/initiate/

    Request body (JSON):
    {
        "product_ids":       [1, 2],
        "shipping_address":  "Thamel, Kathmandu",
        "buyer_name":        "Ram Bahadur",
        "buyer_phone":       "9841000000",
        "shipping_amount":   400,
        "discount_amount":   0
    }

    Response:
    {
        "success": true,
        "payment_url": "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
        "form_data":   { ... },   <- POST these fields to payment_url as an HTML form
        "ref_id":      "AM-3F9A1C2B4E",
        "total":       12400.0
    }
    """
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('Invalid JSON body')

    product_ids      = body.get('product_ids', [])
    shipping_address = body.get('shipping_address', '').strip()
    buyer_name       = body.get('buyer_name', '').strip()
    buyer_phone      = body.get('buyer_phone', '').strip()
    shipping_amount  = float(body.get('shipping_amount', 0))
    discount_amount  = float(body.get('discount_amount', 0))

    if not product_ids or not shipping_address:
        return json_error('product_ids and shipping_address are required')

    products, err = _get_cart_products(request, product_ids)
    if err:
        return err

    subtotal = sum(float(p.price) for p in products)
    total    = round(subtotal + shipping_amount - discount_amount, 2)
    ref_id   = make_ref_id()

    # Create pending orders
    _create_orders(
        request.user, products, shipping_amount, discount_amount,
        total, ref_id, 'esewa', 'pending',
        shipping_address, buyer_name, buyer_phone
    )

    # Build eSewa v2 HMAC-SHA256 signature
    merchant_id = settings.ESEWA_MERCHANT_ID
    secret_key  = settings.ESEWA_SECRET_KEY
    message     = f"total_amount={total},transaction_uuid={ref_id},product_code={merchant_id}"
    signature   = base64.b64encode(
        hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()

    form_data = {
        'amount':                    str(subtotal),
        'tax_amount':                '0',
        'total_amount':              str(total),
        'transaction_uuid':          ref_id,
        'product_code':              merchant_id,
        'product_service_charge':    '0',
        'product_delivery_charge':   str(shipping_amount),
        'success_url':               settings.ESEWA_SUCCESS_URL,
        'failure_url':               settings.ESEWA_FAILURE_URL,
        'signed_field_names':        'total_amount,transaction_uuid,product_code',
        'signature':                 signature,
    }

    return json_success({
        'payment_url': settings.ESEWA_PAYMENT_URL,
        'form_data':   form_data,
        'ref_id':      ref_id,
        'total':       total,
    }, 'eSewa payment initiated — submit the form_data to payment_url')


def api_esewa_verify(request):
    """
    GET /api/payment/esewa/verify/?data=<base64_encoded_response>
    eSewa redirects the user to this URL after payment.
    Django decodes the data, verifies the HMAC signature, and marks orders as paid.
    """
    encoded = request.GET.get('data', '')
    if not encoded:
        return json_error('No payment data received from eSewa', 400)

    try:
        decoded = base64.b64decode(encoded).decode('utf-8')
        data    = json.loads(decoded)
    except Exception:
        return json_error('Could not decode eSewa payment response', 400)

    status         = data.get('status', '')
    ref_id         = data.get('transaction_uuid', '')
    total_amount   = data.get('total_amount', '')
    transaction_id = data.get('transaction_id', '')
    signature      = data.get('signature', '')

    if status != 'COMPLETE':
        Order.objects.filter(payment_ref_id=ref_id).update(
            payment_status='failed', status='cancelled'
        )
        return json_error(f'Payment not completed — eSewa status: {status}', 400)

    # Verify HMAC signature
    merchant_id = settings.ESEWA_MERCHANT_ID
    secret_key  = settings.ESEWA_SECRET_KEY
    message     = f"transaction_id={transaction_id},status={status},total_amount={total_amount},transaction_uuid={ref_id},product_code={merchant_id}"
    expected    = base64.b64encode(
        hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    ).decode()

    if signature != expected:
        return json_error('eSewa signature verification failed — payment rejected', 400)

    # Mark orders as paid
    now    = datetime.now(timezone.utc)
    orders = Order.objects.filter(payment_ref_id=ref_id)
    orders.update(
        payment_status='verified',
        status='paid',
        transaction_id=transaction_id,
        paid_at=now,
    )
    for order in orders:
        order.product.status = 'sold'
        order.product.save()
        Cart.objects.filter(product=order.product).delete()

    first = orders.first()
    return json_success({
        'order_id':       first.pk if first else None,
        'ref_id':         ref_id,
        'transaction_id': transaction_id,
        'total':          total_amount,
        'paid_at':        now.isoformat(),
    }, 'eSewa payment verified successfully')


# ─────────────────────────────────────────────────────────────────
#  PAYMENT — Khalti
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def api_khalti_initiate(request):
    """
    POST /api/payment/khalti/initiate/

    Request body (JSON):
    {
        "product_ids":       [1, 2],
        "shipping_address":  "Thamel, Kathmandu",
        "buyer_name":        "Ram Bahadur",
        "buyer_phone":       "9841000000",
        "shipping_amount":   400,
        "discount_amount":   0
    }

    Response:
    {
        "success":     true,
        "payment_url": "https://pay.khalti.com/?pidx=...",  <- redirect user here
        "pidx":        "...",
        "ref_id":      "AM-3F9A1C2B4E",
        "total":       12400.0
    }
    """
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('Invalid JSON body')

    product_ids      = body.get('product_ids', [])
    shipping_address = body.get('shipping_address', '').strip()
    buyer_name       = body.get('buyer_name', '').strip()
    buyer_phone      = body.get('buyer_phone', '').strip()
    shipping_amount  = float(body.get('shipping_amount', 0))
    discount_amount  = float(body.get('discount_amount', 0))

    if not product_ids or not shipping_address:
        return json_error('product_ids and shipping_address are required')

    products, err = _get_cart_products(request, product_ids)
    if err:
        return err

    subtotal = sum(float(p.price) for p in products)
    total    = round(subtotal + shipping_amount - discount_amount, 2)
    ref_id   = make_ref_id()

    # Create pending orders
    _create_orders(
        request.user, products, shipping_amount, discount_amount,
        total, ref_id, 'khalti', 'pending',
        shipping_address, buyer_name, buyer_phone
    )

    # Call Khalti initiate API
    payload = json.dumps({
        'return_url':          settings.KHALTI_RETURN_URL,
        'website_url':         settings.KHALTI_WEBSITE_URL,
        'amount':              int(total * 100),   # Khalti uses paisa (1 NPR = 100 paisa)
        'purchase_order_id':   ref_id,
        'purchase_order_name': 'Alpha Mart Order',
        'customer_info': {
            'name':  buyer_name,
            'email': request.user.email,
            'phone': buyer_phone,
        },
    }).encode('utf-8')

    req = urllib_req.Request(
        settings.KHALTI_INITIATE_URL,
        data=payload,
        headers={
            'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
            'Content-Type':  'application/json',
        }
    )

    try:
        with urllib_req.urlopen(req) as resp:
            khalti_resp = json.loads(resp.read().decode())

        payment_url = khalti_resp.get('payment_url', '')
        pidx        = khalti_resp.get('pidx', '')

        # Store Khalti's pidx so we can look it up during verification
        Order.objects.filter(payment_ref_id=ref_id).update(transaction_id=pidx)

        return json_success({
            'payment_url': payment_url,
            'pidx':        pidx,
            'ref_id':      ref_id,
            'total':       total,
        }, 'Khalti payment initiated — redirect user to payment_url')

    except Exception as e:
        # Clean up pending orders if Khalti API call failed
        Order.objects.filter(payment_ref_id=ref_id).delete()
        return json_error(f'Khalti API call failed: {str(e)}')


@csrf_exempt
@require_http_methods(['POST'])
def api_khalti_verify(request):
    """
    POST /api/payment/khalti/verify/

    Called by the frontend after Khalti redirects back with ?pidx=...
    Body: { "pidx": "..." }

    Calls Khalti lookup API to confirm payment, then marks orders paid.
    """
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('Invalid JSON body')

    pidx = body.get('pidx', '').strip()
    if not pidx:
        return json_error('pidx is required')

    # Call Khalti lookup API
    payload = json.dumps({'pidx': pidx}).encode('utf-8')
    req     = urllib_req.Request(
        settings.KHALTI_LOOKUP_URL,
        data=payload,
        headers={
            'Authorization': f'key {settings.KHALTI_SECRET_KEY}',
            'Content-Type':  'application/json',
        }
    )

    try:
        with urllib_req.urlopen(req) as resp:
            khalti_resp = json.loads(resp.read().decode())
    except Exception as e:
        return json_error(f'Khalti lookup API call failed: {str(e)}')

    status         = khalti_resp.get('status', '')
    transaction_id = khalti_resp.get('transaction_id', pidx)
    total_paisa    = khalti_resp.get('total_amount', 0)   # in paisa

    if status != 'Completed':
        Order.objects.filter(transaction_id=pidx).update(
            payment_status='failed', status='cancelled'
        )
        return json_error(f'Khalti payment not completed — status: {status}', 400)

    # Mark orders as paid
    now    = datetime.now(timezone.utc)
    orders = Order.objects.filter(transaction_id=pidx)
    orders.update(
        payment_status='verified',
        status='paid',
        transaction_id=transaction_id,
        paid_at=now,
    )
    for order in orders:
        order.product.status = 'sold'
        order.product.save()
        Cart.objects.filter(product=order.product).delete()

    first = orders.first()
    return json_success({
        'order_id':       first.pk if first else None,
        'pidx':           pidx,
        'transaction_id': transaction_id,
        'total_npr':      total_paisa / 100,
        'paid_at':        now.isoformat(),
    }, 'Khalti payment verified successfully')


# ─────────────────────────────────────────────────────────────────
#  PAYMENT — Card (Simulated / Demo)
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def api_card_process(request):
    """
    POST /api/payment/card/process/

    Simulated card payment — always succeeds in demo mode.
    No real card gateway is connected.

    Request body (JSON):
    {
        "product_ids":       [1, 2],
        "shipping_address":  "Thamel, Kathmandu",
        "buyer_name":        "Ram Bahadur",
        "buyer_phone":       "9841000000",
        "shipping_amount":   400,
        "discount_amount":   0,
        "card_number":       "4111111111111111",
        "card_name":         "RAM BAHADUR",
        "expiry":            "12/26",
        "cvv":               "123"
    }
    """
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('Invalid JSON body')

    product_ids      = body.get('product_ids', [])
    shipping_address = body.get('shipping_address', '').strip()
    buyer_name       = body.get('buyer_name', '').strip()
    buyer_phone      = body.get('buyer_phone', '').strip()
    shipping_amount  = float(body.get('shipping_amount', 0))
    discount_amount  = float(body.get('discount_amount', 0))
    card_number      = body.get('card_number', '').replace(' ', '').strip()
    card_name        = body.get('card_name', '').strip()
    expiry           = body.get('expiry', '').strip()
    cvv              = body.get('cvv', '').strip()

    if not product_ids or not shipping_address:
        return json_error('product_ids and shipping_address are required')

    if not card_number or not expiry or not cvv or not card_name:
        return json_error('card_number, card_name, expiry and cvv are all required')

    if not card_number.isdigit() or len(card_number) < 13:
        return json_error('Invalid card number')

    products, err = _get_cart_products(request, product_ids)
    if err:
        return err

    subtotal   = sum(float(p.price) for p in products)
    total      = round(subtotal + shipping_amount - discount_amount, 2)
    ref_id     = make_ref_id()
    txn_id     = 'CARD-SIM-' + uuid.uuid4().hex[:8].upper()
    now        = datetime.now(timezone.utc)

    # Create orders and mark paid immediately (simulation)
    orders = _create_orders(
        request.user, products, shipping_amount, discount_amount,
        total, ref_id, 'card', 'pending',
        shipping_address, buyer_name, buyer_phone
    )
    Order.objects.filter(payment_ref_id=ref_id).update(
        payment_status='verified',
        status='paid',
        transaction_id=txn_id,
        paid_at=now,
    )
    for order in orders:
        order.product.status = 'sold'
        order.product.save()
        Cart.objects.filter(user=request.user, product=order.product).delete()

    return json_success({
        'order_id':       orders[0].pk if orders else None,
        'ref_id':         ref_id,
        'transaction_id': txn_id,
        'total':          total,
        'card_last4':     card_number[-4:],
        'paid_at':        now.isoformat(),
    }, 'Card payment processed (Demo simulation)')


# ─────────────────────────────────────────────────────────────────
#  PAYMENT — COD (Cash on Delivery)
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def api_cod_place(request):
    """
    POST /api/payment/cod/place/

    No payment collected now — order saved as pending.
    Product reserved. Cash collected on delivery by delivery person.
    Only available in Kathmandu Valley.

    Request body (JSON):
    {
        "product_ids":       [1, 2],
        "shipping_address":  "Thamel, Kathmandu",
        "buyer_name":        "Ram Bahadur",
        "buyer_phone":       "9841000000",
        "shipping_amount":   200,
        "discount_amount":   0,
        "area":              "Kathmandu"
    }
    """
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return json_error('Invalid JSON body')

    product_ids      = body.get('product_ids', [])
    shipping_address = body.get('shipping_address', '').strip()
    buyer_name       = body.get('buyer_name', '').strip()
    buyer_phone      = body.get('buyer_phone', '').strip()
    shipping_amount  = float(body.get('shipping_amount', 200))
    discount_amount  = float(body.get('discount_amount', 0))
    area             = body.get('area', '').strip()

    if not product_ids or not shipping_address:
        return json_error('product_ids and shipping_address are required')

    if not area:
        return json_error('COD is only available in Kathmandu Valley — please select an area')

    products, err = _get_cart_products(request, product_ids)
    if err:
        return err

    subtotal = sum(float(p.price) for p in products)
    total    = round(subtotal + shipping_amount - discount_amount, 2)
    ref_id   = make_ref_id()

    # Create orders as pending — no payment yet
    orders = _create_orders(
        request.user, products, shipping_amount, discount_amount,
        total, ref_id, 'cod', 'unpaid',
        f"{area}, {shipping_address}", buyer_name, buyer_phone
    )

    # Reserve products so others cannot buy them while awaiting delivery
    for order in orders:
        order.product.status = 'reserved'
        order.product.save()
        Cart.objects.filter(user=request.user, product=order.product).delete()

    return json_success({
        'order_id': orders[0].pk if orders else None,
        'ref_id':   ref_id,
        'total':    total,
        'area':     area,
    }, 'COD order placed — pay cash when your item is delivered')


# ─────────────────────────────────────────────────────────────────
#  ORDERS
# ─────────────────────────────────────────────────────────────────

def api_orders(request):
    """GET /api/orders/ — list the current user's orders."""
    if not request.user.is_authenticated:
        return json_error('Login required', 401)

    orders = Order.objects.filter(buyer=request.user) \
                          .select_related('product') \
                          .order_by('-created_at')

    data = []
    for o in orders:
        data.append({
            'id':               o.pk,
            'product_id':       o.product.pk,
            'product_name':     o.product.title,
            'amount':           float(o.amount),
            'shipping':         float(o.shipping_amount),
            'discount':         float(o.discount_amount),
            'total':            float(o.total_amount),
            'status':           o.status,
            'payment_method':   o.payment_method,
            'payment_status':   o.payment_status,
            'transaction_id':   o.transaction_id,
            'ref_id':           o.payment_ref_id,
            'shipping_address': o.shipping_address,
            'buyer_name':       o.buyer_name,
            'buyer_phone':      o.buyer_phone,
            'paid_at':          o.paid_at.isoformat() if o.paid_at else None,
            'created_at':       o.created_at.isoformat(),
        })

    return json_ok({'orders': data, 'count': len(data)})