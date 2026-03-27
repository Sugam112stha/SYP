

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings')
django.setup()

from django.contrib.auth.models import User
from myApp.models import Category, Product, UserProfile

print("=" * 50)
print("  AlphaMart Setup Script")
print("=" * 50)

# ── Step 1: Create Categories ──────────────────────────
print("\n📂 Creating categories...")

categories_data = [
    ('Smartphones',  'smartphones',  'fa-mobile-alt'),
    ('Laptops',      'laptops',      'fa-laptop'),
    ('Cameras',      'cameras',      'fa-camera'),
    ('Audio',        'audio',        'fa-headphones'),
    ('Gaming',       'gaming',       'fa-gamepad'),
    ('Tablets',      'tablets',      'fa-tablet-alt'),
    ('Lenses',       'lenses',       'fa-camera-retro'),
    ('Accessories',  'accessories',  'fa-plug'),
    ('Smartwatches', 'smartwatches', 'fa-clock'),
    ('TVs',          'tvs',          'fa-tv'),
]

for name, slug, icon in categories_data:
    cat, created = Category.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'icon': icon}
    )
    if created:
        print(f"  ✅ Created: {name}")
    else:
        print(f"  ⚠️  Already exists: {name}")

# ── Step 2: Create Demo Seller Account ────────────────
print("\n👤 Creating demo seller account...")

demo_seller, created = User.objects.get_or_create(
    username='demo@alphamart.com',
    defaults={
        'email':      'demo@alphamart.com',
        'first_name': 'Demo',
        'last_name':  'Seller',
        'is_active':  True,
    }
)
if created:
    demo_seller.set_password('demo123456')
    demo_seller.save()
    UserProfile.objects.get_or_create(
        user=demo_seller,
        defaults={
            'phone':       '9800000000',
            'address':     'Thamel, Kathmandu',
            'role':        'seller',
            'is_verified': True,
        }
    )
    print("  ✅ Demo seller created: demo@alphamart.com / demo123456")
else:
    print("  ⚠️  Demo seller already exists")

# ── Step 3: Create Demo Products ──────────────────────
print("\n📦 Creating demo products...")

smartphones = Category.objects.get(slug='smartphones')
laptops     = Category.objects.get(slug='laptops')
cameras     = Category.objects.get(slug='cameras')
audio       = Category.objects.get(slug='audio')

demo_products = [
    {
        'title':       'iPhone 13 Pro Max - 256GB Space Grey',
        'description': 'Used for 8 months only. Excellent condition. No scratches. Original box included. Battery health 94%. All accessories included.',
        'price':       95000,
        'condition':   'excellent',
        'category':    smartphones,
        'location':    'Kathmandu',
    },
    {
        'title':       'Samsung Galaxy S22 Ultra - 128GB',
        'description': 'Bought 6 months ago. Good condition with minor scratches on back. S-Pen included. Fast charging adapter included.',
        'price':       75000,
        'condition':   'good',
        'category':    smartphones,
        'location':    'Lalitpur',
    },
    {
        'title':       'MacBook Pro M1 - 8GB RAM 256GB SSD',
        'description': 'Used for 1 year. Excellent condition. Battery cycle count 120. Comes with original charger. No dents or scratches.',
        'price':       145000,
        'condition':   'excellent',
        'category':    laptops,
        'location':    'Kathmandu',
    },
    {
        'title':       'Dell XPS 15 - Intel i7 16GB RAM 512GB',
        'description': 'Professional laptop in good condition. Used for office work. Some keyboard wear but fully functional. Charger included.',
        'price':       85000,
        'condition':   'good',
        'category':    laptops,
        'location':    'Pokhara',
    },
    {
        'title':       'Canon EOS 200D - 24.1MP DSLR Camera',
        'description': 'Shutter count only 5000. Comes with 18-55mm kit lens, bag, and extra battery. Perfect for beginners and professionals.',
        'price':       55000,
        'condition':   'excellent',
        'category':    cameras,
        'location':    'Biratnagar',
    },
    {
        'title':       'Sony WH-1000XM4 Noise Cancelling Headphones',
        'description': 'Used for 3 months. Excellent noise cancellation. All original accessories included. No scratches.',
        'price':       18000,
        'condition':   'excellent',
        'category':    audio,
        'location':    'Kathmandu',
    },
]

created_count = 0
for p_data in demo_products:
    exists = Product.objects.filter(title=p_data['title'], seller=demo_seller).exists()
    if not exists:
        Product.objects.create(
            seller=demo_seller,
            title=p_data['title'],
            description=p_data['description'],
            price=p_data['price'],
            condition=p_data['condition'],
            category=p_data['category'],
            location=p_data['location'],
            status='available',
        )
        created_count += 1
        print(f"  ✅ Created: {p_data['title'][:40]}")
    else:
        print(f"  ⚠️  Already exists: {p_data['title'][:40]}")

print("\n" + "=" * 50)
print("  ✅ Setup Complete!")
print("=" * 50)
print(f"\n  Categories: {Category.objects.count()}")
print(f"  Products:   {Product.objects.count()}")
print(f"\n  Demo seller login:")
print(f"  Email:    demo@alphamart.com")
print(f"  Password: demo123456")
print(f"\n  Run: python manage.py runserver")
print(f"  Open: http://127.0.0.1:8000/")
print("=" * 50) 