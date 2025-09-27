from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging

from payments import models
from .models import Payment, Subscription, Invoice, Refund
from accounts.models import User
from courses.models import Course
from .serializers import (
    PaymentSerializer, 
    PaymentCreateSerializer,
    SubscriptionSerializer, 
    InvoiceSerializer, 
    RefundSerializer,
    PaymentIntentSerializer
)
from .services import PaymentService
from .permissions import IsPaymentOwnerOrAdmin

logger = logging.getLogger(__name__)

class PaymentListCreateView(generics.ListCreateAPIView):
    """Список платежей и создание нового платежа"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'currency', 'student']
    search_fields = ['transaction_id', 'student__username', 'student__email']
    ordering_fields = ['created_at', 'amount', 'paid_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Payment.objects.all()
        elif user.is_student:
            return Payment.objects.filter(student=user)
        elif user.is_parent:
            # Родитель видит платежи своих детей
            children_ids = user.children.values_list('id', flat=True)
            return Payment.objects.filter(student_id__in=children_ids)
        return Payment.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer

class PaymentDetailView(generics.RetrieveUpdateAPIView):
    """Детали платежа"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsPaymentOwnerOrAdmin]

class SubscriptionListCreateView(generics.ListCreateAPIView):
    """Список подписок и создание новой подписки"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'student', 'course']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Subscription.objects.all()
        elif user.is_student:
            return Subscription.objects.filter(student=user)
        elif user.is_parent:
            children_ids = user.children.values_list('id', flat=True)
            return Subscription.objects.filter(student_id__in=children_ids)
        return Subscription.objects.none()

class SubscriptionDetailView(generics.RetrieveUpdateAPIView):
    """Детали подписки"""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated, IsPaymentOwnerOrAdmin]

class InvoiceListView(generics.ListAPIView):
    """Список счетов"""
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'currency', 'student']
    ordering_fields = ['due_date', 'created_at', 'paid_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Invoice.objects.all()
        elif user.is_student:
            return Invoice.objects.filter(student=user)
        elif user.is_parent:
            children_ids = user.children.values_list('id', flat=True)
            return Invoice.objects.filter(student_id__in=children_ids)
        return Invoice.objects.none()

class InvoiceDetailView(generics.RetrieveAPIView):
    """Детали счета"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsPaymentOwnerOrAdmin]

class RefundListCreateView(generics.ListCreateAPIView):
    """Список возвратов и создание нового возврата"""
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'payment__student']
    ordering_fields = ['created_at', 'processed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Refund.objects.all()
        return Refund.objects.none()  # Только администраторы могут видеть возвраты

class RefundDetailView(generics.RetrieveUpdateAPIView):
    """Детали возврата"""
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Создание платежного намерения через ЮKassa"""
    serializer = PaymentIntentSerializer(data=request.data)
    if serializer.is_valid():
        try:
            student_id = serializer.validated_data['student_id']
            course_id = serializer.validated_data.get('course_id')
            amount = serializer.validated_data['amount']
            currency = serializer.validated_data.get('currency', 'RUB')
            description = serializer.validated_data.get('description', '')
            return_url = serializer.validated_data.get('return_url')
            
            # Получаем студента и курс
            student = get_object_or_404(User, id=student_id)
            course = get_object_or_404(Course, id=course_id) if course_id else None
            
            # Проверяем права доступа
            user = request.user
            if not (user.is_admin or student == user or 
                    (user.is_parent and student in user.children.all())):
                return Response({
                    'error': 'Нет прав для создания платежа для этого студента'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Создаем платеж через ЮKassa
            result = PaymentService.create_payment(
                student=student,
                course=course,
                amount=amount,
                currency=currency,
                description=description,
                return_url=return_url
            )
            
            if result['success']:
                return Response({
                    'message': 'Платеж успешно создан',
                    'payment_url': result['payment_url'],
                    'payment_id': result['payment_id']
                })
            else:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment(request):
    """Подтверждение платежа"""
    payment_id = request.data.get('payment_id')
    yookassa_payment_id = request.data.get('yookassa_payment_id')
    
    try:
        payment = Payment.objects.get(id=payment_id)
        
        # Проверка прав доступа
        user = request.user
        if not (user.is_admin or payment.student == user or 
                (user.is_parent and payment.student in user.children.all())):
            return Response({
                'error': 'Нет прав для подтверждения этого платежа'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Подтверждаем платеж через сервис
        result = PaymentService.confirm_payment(yookassa_payment_id)
        
        if result['success']:
            return Response({
                'message': 'Платеж успешно подтвержден',
                'payment': PaymentSerializer(payment).data
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Payment.DoesNotExist:
        return Response({
            'error': 'Платеж не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_refund(request):
    """Обработка возврата"""
    if not request.user.is_admin:
        return Response({
            'error': 'Только администраторы могут обрабатывать возвраты'
        }, status=status.HTTP_403_FORBIDDEN)
    
    refund_id = request.data.get('refund_id')
    action = request.data.get('action')  # 'approve' или 'reject'
    
    try:
        refund = Refund.objects.get(id=refund_id)
        
        if action == 'approve':
            result = PaymentService.process_refund(refund)
            if result['success']:
                return Response({
                    'message': 'Возврат успешно обработан',
                    'refund': RefundSerializer(refund).data
                })
            else:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
        elif action == 'reject':
            refund.status = 'rejected'
            refund.save()
            return Response({
                'message': 'Возврат отклонен',
                'refund': RefundSerializer(refund).data
            })
        else:
            return Response({
                'error': 'Неверное действие. Используйте "approve" или "reject"'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Refund.DoesNotExist:
        return Response({
            'error': 'Возврат не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_payment_history(request, student_id):
    """История платежей студента"""
    user = request.user
    
    # Проверка прав доступа
    if user.is_admin:
        student = get_object_or_404(User, id=student_id, role='student')
    elif user.is_parent:
        student = get_object_or_404(User, id=student_id, role='student', parent=user)
    elif user.is_student and user.id == student_id:
        student = user
    else:
        return Response({
            'error': 'Нет прав для просмотра истории платежей'
        }, status=status.HTTP_403_FORBIDDEN)
    
    payments = Payment.objects.filter(student=student).order_by('-created_at')
    serializer = PaymentSerializer(payments, many=True)
    
    return Response({
        'student': f"{student.get_full_name()} ({student.username})",
        'payments': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_statistics(request):
    """Статистика платежей"""
    if not request.user.is_admin:
        return Response({
            'error': 'Только администраторы могут просматривать статистику'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Общая статистика
    total_payments = Payment.objects.filter(status='paid').count()
    total_amount = Payment.objects.filter(status='paid').aggregate(
        models.Sum('amount')
    )['amount__sum'] or 0
    
    # Статистика по месяцам
    monthly_stats = Payment.objects.filter(
        status='paid',
        paid_at__isnull=False
    ).extra(
        select={'month': "EXTRACT(month FROM paid_at)"}
    ).values('month').annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount')
    ).order_by('month')
    
    # Статистика по курсам
    course_stats = Payment.objects.filter(status='paid').values(
        'course__title'
    ).annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount')
    ).order_by('-total_amount')
    
    return Response({
        'total_payments': total_payments,
        'total_amount': float(total_amount),
        'monthly_stats': list(monthly_stats),
        'course_stats': list(course_stats)
    })

# === WEBHOOK ДЛЯ ЮKASSA ===

@csrf_exempt
@api_view(['POST'])
def yookassa_webhook(request):
    """Webhook для получения уведомлений от ЮKassa"""
    try:
        # Получаем данные из webhook
        data = json.loads(request.body.decode('utf-8'))
        event = data.get('event')
        object_data = data.get('object', {})
        
        logger.info(f"Получено событие от ЮKassa: {event}")
        
        if event == 'payment.succeeded':
            # Платеж успешно проведен
            payment_id = object_data.get('id')
            if payment_id:
                result = PaymentService.confirm_payment(payment_id)
                if result['success']:
                    logger.info(f"Платеж {payment_id} успешно подтвержден")
                else:
                    logger.error(f"Ошибка подтверждения платежа {payment_id}: {result.get('error')}")
        
        elif event == 'payment.canceled':
            # Платеж отменен
            payment_id = object_data.get('id')
            if payment_id:
                # Здесь можно добавить логику обработки отмены
                logger.info(f"Платеж {payment_id} отменен")
        
        # Возвращаем успешный ответ
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook от ЮKassa: {str(e)}")
        return HttpResponse(status=500)

# === ВСПОМОГАТЕЛЬНЫЕ ЭНДПОИНТЫ ===

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_course_price(request, course_id):
    """Получить цену курса"""
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        return Response({
            'course_id': course.id,
            'title': course.title,
            'price': float(course.price),
            'currency': 'RUB'
        })
    except Course.DoesNotExist:
        return Response({
            'error': 'Курс не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_course_payment(request, course_id):
    """Создать платеж за курс"""
    try:
        course = Course.objects.get(id=course_id, is_active=True)
        student = request.user
        
        # Создаем платеж через ЮKassa
        result = PaymentService.create_payment(
            student=student,
            course=course,
            amount=float(course.price),
            currency='RUB',
            description=f"Оплата курса: {course.title}",
            return_url=request.data.get('return_url', 'https://yourdomain.com/payment-success/')
        )
        
        if result['success']:
            return Response({
                'message': 'Платеж успешно создан',
                'payment_url': result['payment_url'],
                'payment_id': result['payment_id']
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Course.DoesNotExist:
        return Response({
            'error': 'Курс не найден'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)