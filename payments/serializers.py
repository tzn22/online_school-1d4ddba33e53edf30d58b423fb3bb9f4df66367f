from rest_framework import serializers
from .models import Payment, Subscription, Invoice, Refund
from accounts.models import User
from courses.models import Course, Group

class PaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True, allow_null=True)
    group_title = serializers.CharField(source='group.title', read_only=True, allow_null=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'paid_at', 
            'transaction_id', 'payment_intent_id'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть больше 0")
        return value

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['student', 'course', 'group', 'amount', 'currency', 'payment_method', 'description']
        read_only_fields = ['status']
    
    def validate(self, attrs):
        course = attrs.get('course')
        group = attrs.get('group')
        amount = attrs.get('amount')
        
        # Проверка соответствия суммы курсу
        if course and amount != course.price:
            raise serializers.ValidationError({
                'amount': f'Сумма должна быть равна цене курса: {course.price}'
            })
        
        # Проверка, что указана либо группа, либо курс
        if not course and not group:
            raise serializers.ValidationError('Необходимо указать курс или группу')
        
        return attrs

class SubscriptionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    group_title = serializers.CharField(source='group.title', read_only=True, allow_null=True)
    
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class InvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    payment_amount = serializers.DecimalField(
        source='payment.amount', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'paid_at', 'invoice_number']

class RefundSerializer(serializers.ModelSerializer):
    payment_amount = serializers.DecimalField(
        source='payment.amount', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    student_name = serializers.CharField(
        source='payment.student.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = Refund
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'processed_at']
    
    def validate_amount(self, value):
        if hasattr(self, 'instance') and self.instance:
            payment_amount = self.instance.payment.amount
        elif self.context.get('payment'):
            payment_amount = self.context['payment'].amount
        else:
            raise serializers.ValidationError("Не удалось определить сумму платежа")
        
        if value > payment_amount:
            raise serializers.ValidationError(f"Сумма возврата не может превышать сумму платежа: {payment_amount}")
        return value

class PaymentIntentSerializer(serializers.Serializer):
    """Сериализатор для создания платежного намерения"""
    student_id = serializers.IntegerField()
    course_id = serializers.IntegerField(required=False)
    group_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='RUB')
    description = serializers.CharField(required=False, allow_blank=True)