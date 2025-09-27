from django.urls import path
from .views import (
    PaymentListCreateView,
    PaymentDetailView,
    SubscriptionListCreateView,
    SubscriptionDetailView,
    InvoiceListView,
    InvoiceDetailView,
    RefundListCreateView,
    RefundDetailView,
    create_payment_intent,
    confirm_payment,
    process_refund,
    student_payment_history,
    payment_statistics,
    yookassa_webhook,
    get_course_price,
    create_course_payment
)

urlpatterns = [
    # Платежи
    path('payments/', PaymentListCreateView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/intent/', create_payment_intent, name='create-payment-intent'),
    path('payments/confirm/', confirm_payment, name='confirm-payment'),
    path('payments/course/<int:course_id>/', create_course_payment, name='create-course-payment'),
    
    # Подписки
    path('subscriptions/', SubscriptionListCreateView.as_view(), name='subscription-list'),
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # Счета
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    
    # Возвраты
    path('refunds/', RefundListCreateView.as_view(), name='refund-list'),
    path('refunds/<int:pk>/', RefundDetailView.as_view(), name='refund-detail'),
    path('refunds/process/', process_refund, name='process-refund'),
    
    # Дополнительные endpoints
    path('students/<int:student_id>/payments/', student_payment_history, name='student-payment-history'),
    path('statistics/', payment_statistics, name='payment-statistics'),
    path('courses/<int:course_id>/price/', get_course_price, name='get-course-price'),
    
    # Webhook для ЮKassa
    path('webhook/yookassa/', yookassa_webhook, name='yookassa-webhook'),
]