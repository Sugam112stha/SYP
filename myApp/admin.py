from django.contrib import admin
from django.utils import timezone
from .models import (
    UserProfile, Category, Product, ProductImage,
    Message, Complaint, Cart, Order,
    SellerEarning, PayoutRequest
)

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Message)
admin.site.register(Complaint)
admin.site.register(Cart)
admin.site.register(Order)


@admin.register(SellerEarning)
class SellerEarningAdmin(admin.ModelAdmin):
    list_display  = ('seller', 'order', 'gross_amount', 'commission', 'net_amount', 'status', 'created_at')
    list_filter   = ('status',)
    list_editable = ('status',)
    actions       = ['mark_available', 'mark_paid_out']

    def mark_available(self, request, queryset):
        queryset.filter(status='pending').update(status='available', released_at=timezone.now())
        self.message_user(request, f'{queryset.count()} earnings marked as Available.')
    mark_available.short_description = '✅ Mark selected as Available (release to seller)'

    def mark_paid_out(self, request, queryset):
        queryset.update(status='paid_out')
        self.message_user(request, f'{queryset.count()} earnings marked as Paid Out.')
    mark_paid_out.short_description = '💸 Mark selected as Paid Out'


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display  = ('seller', 'amount', 'method', 'account_number', 'status', 'created_at')
    list_filter   = ('status', 'method')
    list_editable = ('status',)
    actions       = ['approve_payouts', 'mark_paid', 'reject_payouts']

    def approve_payouts(self, request, queryset):
        queryset.filter(status='pending').update(status='approved')
        self.message_user(request, 'Selected payout requests approved.')
    approve_payouts.short_description = '✅ Approve selected payout requests'

    def mark_paid(self, request, queryset):
        queryset.update(status='paid', processed_at=timezone.now())
        self.message_user(request, 'Selected payouts marked as Paid.')
    mark_paid.short_description = '💸 Mark selected as Paid (money sent)'

    def reject_payouts(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, 'Selected payout requests rejected.')
    reject_payouts.short_description = '❌ Reject selected payout requests'