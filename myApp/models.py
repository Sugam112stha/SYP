from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extra info for each user beyond Django's built-in User model"""

    ROLE_CHOICES = [
        ('buyer',  'Buyer'),
        ('seller', 'Seller'),
    ]

    user         = models.OneToOneField(User, on_delete=models.CASCADE)
    phone        = models.CharField(max_length=20, blank=True)
    address      = models.TextField(blank=True)
    postal_code  = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified  = models.BooleanField(default=False)
    email_token  = models.CharField(max_length=100, blank=True)
    role         = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    @property
    def is_seller(self):
        return self.role == 'seller'

    @property
    def is_buyer(self):
        return self.role == 'buyer'


class Category(models.Model):
    """Product categories: Smartphone, Laptop, Camera, etc."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    """A second-hand electronics listing"""

    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good',      'Good'),
        ('fair',      'Fair'),
        ('poor',      'Poor'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold',      'Sold'),
        ('reserved',  'Reserved'),
    ]

    seller      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    title       = models.CharField(max_length=200)
    description = models.TextField()
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    condition   = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location    = models.CharField(max_length=200, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_main_image(self):
        first = self.images.first()
        return first.image if first else None


class ProductImage(models.Model):
    """Multiple images per product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image   = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.title}"


class Message(models.Model):
    """In-platform chat between buyer and seller"""
    sender   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='messages')
    content  = models.TextField()
    is_read  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} about {self.product}"

    class Meta:
        ordering = ['created_at']


class Complaint(models.Model):
    """Complaint/dispute system"""

    STATUS_CHOICES = [
        ('open',      'Open'),
        ('in_review', 'In Review'),
        ('resolved',  'Resolved'),
        ('closed',    'Closed'),
    ]

    complainant  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_filed')
    against_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_received')
    product      = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    subject      = models.CharField(max_length=200)
    description  = models.TextField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint by {self.complainant} - {self.subject}"


class Cart(models.Model):
    """Shopping cart"""
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s cart - {self.product.title}"

    class Meta:
        unique_together = ('user', 'product')


class Order(models.Model):
    """Completed purchase"""

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('paid',      'Paid'),
        ('completed', 'Completed'),
        ('refunded',  'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    buyer            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product          = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"


class SellerEarning(models.Model):
    """Tracks how much a seller has earned from each sale (after AlphaMart commission)."""

    STATUS_CHOICES = [
        ('pending',   'Pending'),    # Money held by AlphaMart, not yet released
        ('available', 'Available'),  # Ready to withdraw
        ('paid_out',  'Paid Out'),   # AlphaMart has transferred to seller
    ]

    seller       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings')
    order        = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='earning')
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)  # What buyer paid
    commission   = models.DecimalField(max_digits=10, decimal_places=2)  # AlphaMart's cut
    net_amount   = models.DecimalField(max_digits=10, decimal_places=2)  # Seller receives
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at   = models.DateTimeField(auto_now_add=True)
    released_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Earning Rs.{self.net_amount} for {self.seller.first_name} — Order #{self.order.id}"

    class Meta:
        ordering = ['-created_at']


class PayoutRequest(models.Model):
    """Seller requests withdrawal of their available earnings."""

    STATUS_CHOICES = [
        ('pending',  'Pending'),   # Waiting for AlphaMart to process
        ('approved', 'Approved'),  # AlphaMart approved, transfer in progress
        ('paid',     'Paid'),      # Money sent to seller
        ('rejected', 'Rejected'),  # Rejected with reason
    ]

    METHOD_CHOICES = [
        ('esewa',  'eSewa'),
        ('khalti', 'Khalti'),
        ('bank',   'Bank Transfer'),
    ]

    seller         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payout_requests')
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    method         = models.CharField(max_length=20, choices=METHOD_CHOICES)
    account_number = models.CharField(max_length=100)  # eSewa/Khalti number or bank account
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    note           = models.TextField(blank=True)       # Admin note or rejection reason
    created_at     = models.DateTimeField(auto_now_add=True)
    processed_at   = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payout Rs.{self.amount} → {self.seller.first_name} via {self.method}"

    class Meta:
        ordering = ['-created_at']