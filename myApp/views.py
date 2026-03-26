from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import uuid
from .models import Product, ProductImage, Category, Cart, Message, Complaint, Order, UserProfile, SellerEarning, PayoutRequest


# AlphaMart commission rate (10%) — change this anytime
COMMISSION_RATE = 0.10

# ──────────────────────────────────────────────────────────────
#  Helper: cart count for nav badge
# ──────────────────────────────────────────────────────────────



def _send_order_receipt(request, user, cart_items_data, subtotal, shipping, total, payment_method, shipping_address):
    """Send purchase receipt email to buyer."""
    try:
        method_labels = {'esewa': 'eSewa', 'khalti': 'Khalti', 'cod': 'Cash on Delivery'}
        html_msg = render_to_string('myApp/email_receipt.html', {
            'first_name':      user.first_name,
            'items':           cart_items_data,
            'subtotal':        subtotal,
            'shipping':        shipping,
            'total':           total,
            'payment_method':  method_labels.get(payment_method, payment_method),
            'shipping_address': shipping_address,
        })
        send_mail(
            f'Your AlphaMart Order Confirmation — Rs. {total}',
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_msg,
            fail_silently=True,
        )
    except Exception:
        pass  # Never crash checkout because of email


def _cart_count(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).count()
    return 0


def _unread_count(request):
    if request.user.is_authenticated:
        return Message.objects.filter(receiver=request.user, is_read=False).count()
    return 0


# ──────────────────────────────────────────────────────────────
#  PUBLIC PAGES
# ──────────────────────────────────────────────────────────────

def index(request):
    featured_products  = Product.objects.filter(status='available').order_by('-created_at')[:8]
    slideshow_products = Product.objects.filter(status='available').order_by('-created_at')[:5]
    categories         = Category.objects.all()
    latest_product     = Product.objects.filter(status='available').order_by('-created_at').first()
    total_products     = Product.objects.filter(status='available').count()

    # Fallback category icons if DB empty
    icon_cats = [
        ('fa-mobile-alt',  'Smartphones',  'smartphones'),
        ('fa-laptop',      'Laptops',      'laptops'),
        ('fa-camera',      'Cameras',      'cameras'),
        ('fa-headphones',  'Audio',        'audio'),
        ('fa-gamepad',     'Gaming',       'gaming'),
        ('fa-tablet-alt',  'Tablets',      'tablets'),
    ]

    return render(request, 'myApp/index.html', {
        'featured_products':  featured_products,
        'slideshow_products': slideshow_products,
        'categories':         categories,
        'latest_product':     latest_product,
        'total_products':     total_products,
        'icon_cats':          icon_cats,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


def products_view(request):
    products = Product.objects.all().order_by('-created_at')

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    category_slug = request.GET.get('category', '')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    condition = request.GET.get('condition', '')
    if condition:
        products = products.filter(condition=condition)

    status = request.GET.get('status', '')
    if status:
        products = products.filter(status=status)

    # Sort
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')

    categories = Category.objects.all()
    return render(request, 'myApp/products.html', {
        'products':       products,
        'categories':     categories,
        'query':          query,
        'cart_count':     _cart_count(request),
        'current_sort':   sort,
        'current_cat':    category_slug,
        'current_cond':   condition,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    images  = product.images.all()
    related = Product.objects.filter(
        category=product.category, status='available'
    ).exclude(pk=pk)[:4]

    # Count existing messages between this buyer and seller about this product
    existing_thread = 0
    if request.user.is_authenticated and request.user != product.seller:
        existing_thread = Message.objects.filter(
            product=product
        ).filter(
            Q(sender=request.user, receiver=product.seller) |
            Q(sender=product.seller, receiver=request.user)
        ).count()

    return render(request, 'myApp/product-detail.html', {
        'product':         product,
        'images':          images,
        'related':         related,
        'existing_thread': existing_thread,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


def categories_view(request):
    categories = Category.objects.all()
    return render(request, 'myApp/categories.html', {
        'categories': categories,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


def deals(request):
    products = Product.objects.filter(status='available').order_by('-created_at')[:12]
    return render(request, 'myApp/deals.html', {
        'products':   products,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


def about(request):
    return render(request, 'myApp/about.html', {
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if not all([name, email, message_text]):
            messages.error(request, 'Please fill in all required fields.')
        else:
            # In a real project you'd send an email here
            messages.success(request, f'Thank you {name}! Your message has been received. We will reply to {email} soon.')
            return redirect('contact')

    return render(request, 'myApp/contact.html', {
        'cart_count': _cart_count(request),
        'user_name':  request.user.get_full_name() if request.user.is_authenticated else '',
        'user_email': request.user.email if request.user.is_authenticated else '',
    })


def faq(request):
    return render(request, 'myApp/faq.html', {
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


def terms(request):
    return render(request, 'myApp/terms.html', {
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


# ──────────────────────────────────────────────────────────────
#  AUTHENTICATION
# ──────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip().lower()
        phone      = request.POST.get('phone', '').strip()
        address    = request.POST.get('address', '').strip()
        city       = request.POST.get('city', '').strip()
        postal     = request.POST.get('postal_code', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        # Validation
        if not all([first_name, last_name, email, phone, password1, password2]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'myApp/register.html', {'cart_count': 0})

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'myApp/register.html', {'cart_count': 0})

        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'myApp/register.html', {'cart_count': 0})

        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'myApp/register.html', {'cart_count': 0})

        # Create user — inactive until email verified
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        # ── Email verification disabled until real Gmail is configured ──
        # user.is_active = False  ← uncomment when Gmail is ready
        user.is_active = True  # Temporary: activate immediately for testing without email setup later comment it.
        user.save()

        full_address = f"{address}, {city}" if city else address
        UserProfile.objects.create(
            user=user,
            phone=phone,
            address=full_address,
            postal_code=postal,
            is_verified=True,
        )

        # ── Uncomment below when real Gmail is configured ──────────
        # token = str(uuid.uuid4())
        # profile.email_token = token
        # profile.save()
        # verify_url = request.build_absolute_uri(f'/verify-email/{token}/')
        # send_mail('Verify your AlphaMart account', '',
        #     settings.DEFAULT_FROM_EMAIL, [email],
        #     html_message=render_to_string('myApp/email_verify.html',
        #         {'first_name': first_name, 'verify_url': verify_url}))
        # messages.success(request, f'Check {email} to verify your account.')
        # return redirect('login')
        # ───────────────────────────────────────────────────────────

        login(request, user)
        messages.success(request, f'Welcome to AlphaMart, {first_name}! Your account has been created.')
        return redirect('index')

    return render(request, 'myApp/register.html', {'cart_count': 0})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Check email verified
            # Email verification check disabled until real Gmail configured
            # if not user.is_active:
            #     messages.error(request, 'Please verify your email.')
            #     return render(request, 'myApp/login.html', {'cart_count': 0})
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password. Please try again.')

    return render(request, 'myApp/login.html', {'cart_count': 0})


def verify_email(request, token):
    """Activate account when user clicks email link."""
    try:
        profile = UserProfile.objects.get(email_token=token)
        if profile.user.is_active:
            messages.info(request, 'Your email is already verified. Please log in.')
        else:
            profile.user.is_active = True
            profile.user.save()
            profile.is_verified = True
            profile.email_token  = ''   # invalidate token
            profile.save()
            messages.success(request, f'Email verified! Welcome to AlphaMart, {profile.user.first_name}. You can now log in.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('login')


def resend_verification(request):
    """Resend verification email if user didn't receive it."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(username=email, is_active=False)
            profile = user.userprofile
            if not profile.email_token:
                profile.email_token = str(uuid.uuid4())
                profile.save()
            verify_url = request.build_absolute_uri(f'/verify-email/{profile.email_token}/')
            html_msg = render_to_string('myApp/email_verify.html', {
                'first_name': user.first_name,
                'verify_url': verify_url,
            })
            send_mail('Verify your AlphaMart account', '', settings.DEFAULT_FROM_EMAIL,
                      [email], html_message=html_msg, fail_silently=True)
            messages.success(request, f'Verification email resent to {email}.')
        except User.DoesNotExist:
            messages.error(request, 'No unverified account found with that email.')
    return redirect('login')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')


# ──────────────────────────────────────────────────────────────
#  PROTECTED PAGES
# ──────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    my_products = Product.objects.filter(seller=request.user).order_by('-created_at')
    my_orders   = Order.objects.filter(buyer=request.user).order_by('-created_at')
    unread_msgs = Message.objects.filter(receiver=request.user, is_read=False).count()

    active_listings = my_products.filter(status='available').count()
    sold_listings   = my_products.filter(status='sold').count()
    total_spent     = sum(o.amount for o in my_orders)

    # Seller earnings
    my_earnings      = SellerEarning.objects.filter(seller=request.user)
    total_earned     = sum(e.net_amount for e in my_earnings)
    pending_earnings = sum(e.net_amount for e in my_earnings.filter(status='pending'))
    available_bal    = sum(e.net_amount for e in my_earnings.filter(status='available'))
    paid_out_total   = sum(e.net_amount for e in my_earnings.filter(status='paid_out'))
    my_payouts       = PayoutRequest.objects.filter(seller=request.user)
    commission_rate  = int(COMMISSION_RATE * 100)

    return render(request, 'myApp/dashboard.html', {
        'my_products':      my_products,
        'my_orders':        my_orders,
        'unread_msgs':      unread_msgs,
        'active_listings':  active_listings,
        'sold_listings':    sold_listings,
        'total_spent':      total_spent,
        'total_earned':     total_earned,
        'pending_earnings': pending_earnings,
        'available_bal':    available_bal,
        'paid_out_total':   paid_out_total,
        'my_earnings':      my_earnings,
        'my_payouts':       my_payouts,
        'commission_rate':  commission_rate,
        'cart_count':       _cart_count(request),
        'unread_msg_count': _unread_count(request),
        'profile':          profile,
    })


@login_required
def sell(request):
    # Only sellers can list products
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.role != 'seller':
        messages.error(request, 'Switch to Seller mode in your Profile to list items.')
        return redirect('dashboard')

    categories = Category.objects.all()

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        price       = request.POST.get('price', '')
        condition   = request.POST.get('condition', '')
        category_id = request.POST.get('category', '')
        location    = request.POST.get('location', '').strip()
        images      = request.FILES.getlist('images')

        errors = []
        if not all([title, description, price, condition, category_id]):
            errors.append('Please fill in all required fields.')
        if not images:
            errors.append('Please upload at least one photo.')
        if len(images) > 10:
            errors.append('Maximum 10 photos allowed.')
        try:
            float(price)
            if float(price) <= 0:
                errors.append('Price must be greater than 0.')
        except (ValueError, TypeError):
            if price:
                errors.append('Enter a valid price.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'myApp/sell.html', {
                'categories': categories,
                'cart_count': _cart_count(request),
            'unread_msg_count': _unread_count(request),
            })

        try:
            category = Category.objects.get(pk=category_id)
            product  = Product.objects.create(
                seller=request.user,
                category=category,
                title=title,
                description=description,
                price=price,
                condition=condition,
                location=location,
            )
            for i, img in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_main=(i == 0),
                )
            messages.success(request, f'"{title}" has been listed successfully!')
            return redirect('product_detail', pk=product.pk)

        except Exception as e:
            messages.error(request, f'Something went wrong: {str(e)}')

    return render(request, 'myApp/sell.html', {
        'categories': categories,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product', 'product__category')
    subtotal   = sum(item.product.price for item in cart_items)
    shipping   = 0  # Free for now (COD handled at checkout)
    total      = subtotal + shipping

    return render(request, 'myApp/cart.html', {
        'cart_items': cart_items,
        'subtotal':   subtotal,
        'shipping':   shipping,
        'total':      total,
        'cart_count': cart_items.count(),
    })


@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Only buyers can add to cart
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.role != 'buyer':
        messages.error(request, 'Switch to Buyer mode in your Profile to purchase items.')
        return redirect('product_detail', pk=pk)

    if product.status != 'available':
        messages.error(request, 'Sorry, this item is no longer available.')
        return redirect('product_detail', pk=pk)

    if product.seller == request.user:
        messages.error(request, "You can't add your own listing to cart.")
        return redirect('product_detail', pk=pk)

    obj, created = Cart.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f'"{product.title}" added to cart!')
    else:
        messages.info(request, 'This item is already in your cart.')

    return redirect('cart')


@login_required
def remove_from_cart(request, pk):
    Cart.objects.filter(user=request.user, product_id=pk).delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')

    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    subtotal = sum(item.product.price for item in cart_items)

    # Nepal shipping logic
    profile    = getattr(request.user, 'userprofile', None)
    user_city  = (profile.address or '').lower() if profile else ''
    ktm_cities = ['kathmandu', 'lalitpur', 'bhaktapur', 'patan', 'kirtipur']
    in_valley  = any(city in user_city for city in ktm_cities)

    def calc_shipping(method, amount):
        """
        Free if subtotal >= Rs. 1,00,000 (applies to ALL payment methods).
        Otherwise: COD = Rs.200 valley / Rs.400 outside.
        eSewa/Khalti below threshold still charge delivery.
        """
        if amount >= 100000:
            return 0
        return 200 if in_valley else 400

    payment_method = request.POST.get('payment_method', '') or request.GET.get('method', 'cod')
    shipping = calc_shipping(payment_method, subtotal)
    total    = subtotal + shipping

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '').strip()
        payment_method   = request.POST.get('payment_method', 'cod').strip()
        # Recalculate with actual posted payment method
        shipping = calc_shipping(payment_method, subtotal)
        total    = subtotal + shipping

        if not shipping_address:
            messages.error(request, 'Please provide a delivery address.')
            return render(request, 'myApp/checkout.html', {
                'cart_items': cart_items, 'subtotal': subtotal,
                'shipping': shipping, 'total': total, 'cart_count': cart_items.count(),
            })

        # Create orders + seller earnings
        for item in cart_items:
            order = Order.objects.create(
                buyer=request.user,
                product=item.product,
                amount=item.product.price,
                status='paid',
                shipping_address=shipping_address,
            )
            send_buyer_confirmation(order)
            send_seller_notification(order)

            
            item.product.status = 'sold'
            item.product.save()

            # Calculate commission and create seller earning record
            gross      = item.product.price
            commission = round(gross * COMMISSION_RATE, 2)
            net        = round(gross - commission, 2)
            SellerEarning.objects.create(
                seller       = item.product.seller,
                order        = order,
                gross_amount = gross,
                commission   = commission,
                net_amount   = net,
                status       = 'pending',  # Released after delivery confirmed
            )

        # Snapshot items before deleting for receipt email
        receipt_items = [{'title': i.product.title, 'price': i.product.price} for i in cart_items]
        cart_items.delete()

        # Send receipt email
        _send_order_receipt(request, request.user, receipt_items, subtotal, shipping, total, payment_method, shipping_address)

        # Payment routing
        if payment_method == 'esewa':
            import hashlib, hmac, uuid
            txn_uuid   = str(uuid.uuid4())[:20]
            amount_str = str(int(total))
            secret     = '8gBm/:&EnhH.1/q'
            msg        = f"total_amount={amount_str},transaction_uuid={txn_uuid},product_code=EPAYTEST"
            sig        = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
            import base64
            signature  = base64.b64encode(sig).decode()

            import urllib.parse
            params = urllib.parse.urlencode({
                'amount':           amount_str,
                'failure_url':      request.build_absolute_uri('/dashboard/'),
                'product_delivery_charge': '0',
                'product_service_charge':  '0',
                'product_code':     'EPAYTEST',
                'signature':        signature,
                'signed_field_names': 'total_amount,transaction_uuid,product_code',
                'success_url':      request.build_absolute_uri('/dashboard/'),
                'tax_amount':       '0',
                'total_amount':     amount_str,
                'transaction_uuid': txn_uuid,
            })
            from django.shortcuts import HttpResponseRedirect
            return HttpResponseRedirect(f'https://rc-epay.esewa.com.np/api/epay/main/v2/form?{params}')

        elif payment_method == 'khalti':
            import requests as req_lib, uuid
            payload = {
                'return_url':    request.build_absolute_uri('/dashboard/'),
                'website_url':   request.build_absolute_uri('/'),
                'amount':        int(total) * 100,   # paisa
                'purchase_order_id': str(uuid.uuid4())[:20],
                'purchase_order_name': f'AlphaMart Order',
                'customer_info': {
                    'name':  request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                },
            }
            headers = {
                'Authorization': 'Key test_secret_key_dc74e0fd57cb46cd93832aee0a390234',
                'Content-Type':  'application/json',
            }
            try:
                resp = req_lib.post(
                    'https://a.khalti.com/api/v2/epayment/initiate/',
                    json=payload, headers=headers, timeout=10
                )
                data = resp.json()
                if resp.status_code == 200 and 'payment_url' in data:
                    from django.shortcuts import HttpResponseRedirect
                    return HttpResponseRedirect(data['payment_url'])
                else:
                    messages.error(request, f"Khalti error: {data.get('detail', 'Could not initiate payment.')}")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Khalti connection failed: {e}')
                return redirect('dashboard')

        else:  # COD
            messages.success(request, 'Order placed! Cash on Delivery confirmed. Estimated delivery: 3–5 working days.')
            return redirect('dashboard')

    return render(request, 'myApp/checkout.html', {
        'cart_items':  cart_items,
        'subtotal':    subtotal,
        'shipping':    shipping,
        'total':       total,
        'in_valley':   in_valley,
        'cart_count':  cart_items.count(),
        'user_address': profile.address if profile else '',
    })


@login_required
def send_message(request, product_pk):
    """Buyer sends a message to seller about a product."""
    product = get_object_or_404(Product, pk=product_pk)

    if request.method != 'POST':
        return redirect('product_detail', pk=product_pk)

    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, 'Message cannot be empty.')
        return redirect('product_detail', pk=product_pk)

    # Prevent messaging yourself
    if request.user == product.seller:
        messages.error(request, 'You cannot message yourself.')
        return redirect('product_detail', pk=product_pk)

    Message.objects.create(
        sender=request.user,
        receiver=product.seller,
        product=product,
        content=content,
    )
    messages.success(request, f'Message sent to {product.seller.first_name}!')
    return redirect('conversation', product_pk=product_pk, other_pk=product.seller.pk)


@login_required
def seller_reply(request, product_pk, buyer_pk):
    """Seller replies to a buyer's message about a product."""
    product = get_object_or_404(Product, pk=product_pk)
    buyer   = get_object_or_404(User, pk=buyer_pk)

    if request.method != 'POST':
        return redirect('conversation', product_pk=product_pk, other_pk=buyer_pk)

    content = request.POST.get('content', '').strip()
    if not content:
        messages.error(request, 'Reply cannot be empty.')
        return redirect('conversation', product_pk=product_pk, other_pk=buyer_pk)

    # Receiver is whoever is NOT the current user in this conversation
    receiver = buyer if request.user == product.seller else product.seller

    Message.objects.create(
        sender=request.user,
        receiver=receiver,
        product=product,
        content=content,
    )
    return redirect('conversation', product_pk=product_pk, other_pk=buyer_pk)


@login_required
def conversation(request, product_pk, other_pk):
    """Full conversation thread between two users about a product."""
    product    = get_object_or_404(Product, pk=product_pk)
    other_user = get_object_or_404(User, pk=other_pk)

    # Get all messages between current user and other_user about this product
    thread = Message.objects.filter(
        product=product
    ).filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')

    # Mark received messages as read
    thread.filter(receiver=request.user, is_read=False).update(is_read=True)

    # Determine if current user is buyer or seller in this conversation
    is_seller = (request.user == product.seller)

    return render(request, 'myApp/conversation.html', {
        'product':    product,
        'other_user': other_user,
        'thread':     thread,
        'is_seller':  is_seller,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


@login_required
def messages_view(request):
    """Inbox — grouped by product+partner conversation."""
    all_msgs = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related('product', 'sender', 'receiver').order_by('-created_at')

    # Group into unique conversations: (product, other_user)
    seen = set()
    conversations = []
    for msg in all_msgs:
        other = msg.receiver if msg.sender == request.user else msg.sender
        key   = (msg.product_id, other.pk)
        if key not in seen:
            seen.add(key)
            unread = Message.objects.filter(
                product=msg.product, sender=other,
                receiver=request.user, is_read=False
            ).count()
            conversations.append({
                'product':    msg.product,
                'other_user': other,
                'last_msg':   msg,
                'unread':     unread,
            })

    return render(request, 'myApp/messages.html', {
        'conversations': conversations,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


@login_required
def request_payout(request):
    """Seller requests withdrawal of available balance."""
    if request.method != 'POST':
        return redirect('dashboard')

    available_bal = sum(
        e.net_amount for e in SellerEarning.objects.filter(
            seller=request.user, status='available'
        )
    )

    amount_str     = request.POST.get('amount', '').strip()
    method         = request.POST.get('method', '').strip()
    account_number = request.POST.get('account_number', '').strip()

    if not all([amount_str, method, account_number]):
        messages.error(request, 'Please fill in all payout fields.')
        return redirect('dashboard')

    try:
        amount = round(float(amount_str), 2)
    except ValueError:
        messages.error(request, 'Invalid amount.')
        return redirect('dashboard')

    if amount <= 0:
        messages.error(request, 'Amount must be greater than 0.')
        return redirect('dashboard')

    if amount > float(available_bal):
        messages.error(request, f'Insufficient balance. Available: Rs. {available_bal}')
        return redirect('dashboard')

    # Minimum payout Rs. 500
    if amount < 500:
        messages.error(request, 'Minimum payout amount is Rs. 500.')
        return redirect('dashboard')

    PayoutRequest.objects.create(
        seller         = request.user,
        amount         = amount,
        method         = method,
        account_number = account_number,
        status         = 'pending',
    )
    messages.success(request, f'Payout request of Rs. {amount} submitted! AlphaMart will process within 2–3 working days.')
    return redirect('dashboard')


@login_required
def complaints_view(request):
    my_complaints = Complaint.objects.filter(complainant=request.user).order_by('-created_at')

    if request.method == 'POST':
        subject      = request.POST.get('subject', '').strip()
        description  = request.POST.get('description', '').strip()
        product_id   = request.POST.get('product_id', '').strip()

        if not all([subject, description]):
            messages.error(request, 'Please fill in the subject and description.')
        else:
            product      = None
            against_user = None
            if product_id:
                try:
                    product      = Product.objects.get(pk=int(product_id))
                    against_user = product.seller
                except (Product.DoesNotExist, ValueError):
                    messages.error(request, 'Product not found. Please check the Product ID.')
                    return redirect('complaints')

            if against_user is None:
                # Generic complaint not tied to a product — use admin as target
                try:
                    against_user = User.objects.filter(is_superuser=True).first() or request.user
                except Exception:
                    against_user = request.user

            Complaint.objects.create(
                complainant=request.user,
                against_user=against_user,
                product=product,
                subject=subject,
                description=description,
            )
            messages.success(request, 'Complaint submitted! We will review it within 48 hours.')
            return redirect('complaints')

    return render(request, 'myApp/complaints.html', {
        'my_complaints': my_complaints,
        'cart_count': _cart_count(request),
    'unread_msg_count': _unread_count(request),
    })


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    title   = product.title
    product.delete()
    messages.success(request, f'"{title}" has been deleted.')
    return redirect('dashboard')


@login_required
def update_profile(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name  = request.POST.get('last_name', '').strip()
        request.user.save()

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.phone       = request.POST.get('phone', '').strip()
        profile.address     = request.POST.get('address', '').strip()
        profile.postal_code = request.POST.get('postal_code', '').strip()
        profile.save()

        new_pw = request.POST.get('new_password', '').strip()
        if new_pw:
            if len(new_pw) < 8:
                messages.error(request, 'New password must be at least 8 characters.')
                return redirect('dashboard')
            request.user.set_password(new_pw)
            request.user.save()
            login(request, request.user)
            messages.success(request, 'Profile and password updated successfully!')
        else:
            messages.success(request, 'Profile updated successfully!')

    return redirect('dashboard')


@login_required
def toggle_role(request):
    """Switch user between buyer and seller roles."""
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        new_role = request.POST.get('role', '').strip()
        if new_role in ('buyer', 'seller'):
            profile.role = new_role
            profile.save()
            label = 'Seller' if new_role == 'seller' else 'Buyer'
            messages.success(request, f'Role switched to {label} successfully!')
        else:
            messages.error(request, 'Invalid role selection.')
    return redirect('dashboard')



from django.core.mail import send_mail
from django.conf import settings

# Buyer Email
def send_buyer_confirmation(order):
    buyer_email = order.buyer.email
    buyer_name = order.buyer.username
    product_name = order.product.title
    price = order.amount

    subject = "Order Confirmation"

    message = f"""
Hello {buyer_name},

Your order has been placed successfully.

Product: {product_name}
Price: {price}

Thank you for shopping with us.

Regards,
Marketplace Team
"""

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [buyer_email], fail_silently=False)

# Seller Email
def send_seller_notification(order):
    seller_email = order.product.seller.email
    seller_name = order.product.seller.username
    product_name = order.product.title
    buyer_name = order.buyer.username

    subject = "Your Product Has Been Sold"

    message = f"""
Hello {seller_name},

Good news! 🎉

Your product "{product_name}" has been purchased by {buyer_name}.

Please check your dashboard for order details.

Regards,
Marketplace Team
"""

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [seller_email], fail_silently=False)