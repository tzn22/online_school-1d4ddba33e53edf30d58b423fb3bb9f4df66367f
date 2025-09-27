from django.contrib import admin
from .models import Payment, Subscription, Invoice, Refund

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'course', 'amount', 'currency', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['student__username', 'student__email', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'paid_at']
    date_hierarchy = 'created_at'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['student__username', 'course__title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'student', 'amount', 'currency', 'due_date', 'status']
    list_filter = ['status', 'currency', 'due_date']
    search_fields = ['invoice_number', 'student__username']
    readonly_fields = ['created_at', 'updated_at', 'paid_at']
    date_hierarchy = 'due_date'

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'payment', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['payment__id', 'payment__student__username']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']