from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal

User = settings.AUTH_USER_MODEL

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('В ожидании')),
        ('paid', _('Оплачено')),
        ('failed', _('Ошибка')),
        ('refunded', _('Возвращено')),
        ('cancelled', _('Отменено')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', _('Банковская карта')),
        ('bank_transfer', _('Банковский перевод')),
        ('paypal', _('PayPal')),
        ('stripe', _('Stripe')),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Студент')
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True,
        verbose_name=_('Курс')
    )
    group = models.ForeignKey(
        'courses.Group',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True,
        verbose_name=_('Группа')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Сумма')
    )
    currency = models.CharField(
        max_length=3,
        default='RUB',
        verbose_name=_('Валюта')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='card',
        verbose_name=_('Метод оплаты')
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Статус')
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('ID транзакции')
    )
    payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('ID платежного намерения')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата оплаты')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    
    class Meta:
        verbose_name = _('Платеж')
        verbose_name_plural = _('Платежи')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Платеж #{self.id} - {self.student} - {self.amount} {self.currency}"
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_failed(self):
        return self.status == 'failed'

class Subscription(models.Model):
    SUBSCRIPTION_STATUS_CHOICES = [
        ('active', _('Активна')),
        ('inactive', _('Неактивна')),
        ('cancelled', _('Отменена')),
        ('expired', _('Истекла')),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Студент')
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Курс')
    )
    group = models.ForeignKey(
        'courses.Group',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        null=True,
        blank=True,
        verbose_name=_('Группа')
    )
    start_date = models.DateField(
        verbose_name=_('Дата начала')
    )
    end_date = models.DateField(
        verbose_name=_('Дата окончания')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    
    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Подписка {self.student} на {self.course}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now().date() > self.end_date
    
    def save(self, *args, **kwargs):
        if self.is_expired:
            self.is_active = False
        super().save(*args, **kwargs)

class Invoice(models.Model):
    INVOICE_STATUS_CHOICES = [
        ('draft', _('Черновик')),
        ('sent', _('Отправлен')),
        ('paid', _('Оплачен')),
        ('overdue', _('Просрочен')),
        ('cancelled', _('Отменен')),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='invoices',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Студент')
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='invoice',
        null=True,
        blank=True,
        verbose_name=_('Платеж')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Сумма')
    )
    currency = models.CharField(
        max_length=3,
        default='RUB',
        verbose_name=_('Валюта')
    )
    due_date = models.DateField(
        verbose_name=_('Срок оплаты')
    )
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS_CHOICES,
        default='draft',
        verbose_name=_('Статус')
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Номер счета')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Описание')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата оплаты')
    )
    
    class Meta:
        verbose_name = _('Счет')
        verbose_name_plural = _('Счета')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Счет {self.invoice_number} - {self.amount} {self.currency}"

class Refund(models.Model):
    REFUND_STATUS_CHOICES = [
        ('pending', _('В ожидании')),
        ('approved', _('Одобрен')),
        ('rejected', _('Отклонен')),
        ('processed', _('Обработан')),
    ]
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name=_('Платеж')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Сумма возврата')
    )
    reason = models.TextField(
        verbose_name=_('Причина возврата')
    )
    status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default='pending',
        verbose_name=_('Статус')
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата обработки')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )
    
    class Meta:
        verbose_name = _('Возврат')
        verbose_name_plural = _('Возвраты')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Возврат {self.amount} для платежа #{self.payment.id}"