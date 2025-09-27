import uuid
from decimal import Decimal
from yookassa import Configuration, Payment
from yookassa.domain.models import Amount, Receipt, ReceiptItem
from yookassa.domain.request import PaymentRequest
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from .models import Payment as PaymentModel, Invoice, Refund
from accounts.models import User
from courses.models import Course, Group
import logging

logger = logging.getLogger(__name__)

# Настройка ЮKassa
Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

class PaymentService:
    """Сервис для обработки платежей через ЮKassa"""
    
    @staticmethod
    def create_payment(student, course, amount, currency='RUB', description='', return_url=None):
        """Создание платежа через ЮKassa"""
        try:
            # Генерируем уникальный ID для платежа
            payment_id = str(uuid.uuid4())
            
            # Создаем платеж в ЮKassa
            payment_data = PaymentRequest({
                "amount": {
                    "value": str(amount),
                    "currency": currency
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or settings.YOOKASSA_RETURN_URL
                },
                "capture": True,
                "description": description or f"Оплата курса: {course.title}",
                "metadata": {
                    "payment_id": payment_id,
                    "student_id": student.id,
                    "course_id": course.id if course else "",
                },
                "receipt": {
                    "customer": {
                        "email": student.email
                    },
                    "items": [
                        {
                            "description": course.title if course else "Оплата обучения",
                            "quantity": "1.00",
                            "amount": {
                                "value": str(amount),
                                "currency": currency
                            },
                            "vat_code": "1"  # Без НДС
                        }
                    ]
                }
            })
            
            # Отправляем запрос в ЮKassa
            yookassa_payment = Payment.create(payment_data)
            
            # Создаем платеж в нашей системе
            payment = PaymentModel.objects.create(
                student=student,
                course=course,
                amount=amount,
                currency=currency,
                status='pending',
                transaction_id=yookassa_payment.id,
                description=description,
                payment_method='yookassa',
                external_payment_id=payment_id
            )
            
            return {
                'success': True,
                'payment_url': yookassa_payment.confirmation.confirmation_url,
                'payment_id': payment.id,
                'external_payment_id': payment_id,
                'yookassa_payment_id': yookassa_payment.id
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания платежа в ЮKassa: {str(e)}")
            return {
                'success': False,
                'error': f"Ошибка создания платежа: {str(e)}"
            }
    
    @staticmethod
    def confirm_payment(yookassa_payment_id):
        """Подтверждение платежа через webhook от ЮKassa"""
        try:
            # Получаем информацию о платеже из ЮKassa
            yookassa_payment = Payment.find_one(yookassa_payment_id)
            
            # Находим наш платеж по внешнему ID
            payment = PaymentModel.objects.filter(
                transaction_id=yookassa_payment.id
            ).first()
            
            if not payment:
                logger.error(f"Платеж не найден: {yookassa_payment_id}")
                return {
                    'success': False,
                    'error': 'Платеж не найден'
                }
            
            # Обновляем статус платежа
            if yookassa_payment.status == 'succeeded':
                payment.status = 'paid'
                payment.paid_at = timezone.now()
                payment.save()
                
                # Зачисляем студента на курс
                PaymentService._enroll_student_in_course(payment)
                
                # Создаем счет
                PaymentService._create_invoice(payment)
                
                logger.info(f"Платеж успешно подтвержден: {payment.id}")
                return {'success': True}
                
            elif yookassa_payment.status == 'canceled':
                payment.status = 'failed'
                payment.failed_at = timezone.now()
                payment.save()
                
                logger.info(f"Платеж отменен: {payment.id}")
                return {
                    'success': True,
                    'message': 'Платеж отменен'
                }
                
            else:
                logger.warning(f"Неизвестный статус платежа: {yookassa_payment.status}")
                return {
                    'success': False,
                    'error': f'Неизвестный статус платежа: {yookassa_payment.status}'
                }
                
        except Exception as e:
            logger.error(f"Ошибка подтверждения платежа: {str(e)}")
            return {
                'success': False,
                'error': f"Ошибка подтверждения платежа: {str(e)}"
            }
    
    @staticmethod
    def _enroll_student_in_course(payment):
        """Зачисление студента на курс после оплаты"""
        try:
            if payment.course:
                # Ищем группу по умолчанию для курса
                group = Group.objects.filter(
                    course=payment.course,
                    is_active=True
                ).first()
                
                if group:
                    # Добавляем студента в группу
                    group.students.add(payment.student)
                    logger.info(f"Студент {payment.student.username} зачислен в группу {group.title}")
                
                # Создаем подписку (если нужна)
                # Здесь можно добавить логику подписки
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка зачисления студента на курс: {str(e)}")
            return False
    
    @staticmethod
    def _create_invoice(payment):
        """Создание счета для платежа"""
        try:
            invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{payment.id}"
            
            invoice = Invoice.objects.create(
                student=payment.student,
                payment=payment,
                amount=payment.amount,
                currency=payment.currency,
                due_date=timezone.now().date(),
                status='paid',
                invoice_number=invoice_number,
                description=payment.description,
                paid_at=payment.paid_at
            )
            
            logger.info(f"Создан счет: {invoice.invoice_number}")
            return invoice
            
        except Exception as e:
            logger.error(f"Ошибка создания счета: {str(e)}")
            return None
    
    @staticmethod
    def create_refund(payment, amount=None, reason=''):
        """Создание возврата средств"""
        try:
            if not payment.is_paid:
                return {
                    'success': False,
                    'error': 'Невозможно вернуть средства за неоплаченный платеж'
                }
            
            # Создаем возврат в ЮKassa
            refund_amount = amount or payment.amount
            
            refund_data = {
                "amount": {
                    "value": str(refund_amount),
                    "currency": payment.currency
                },
                "payment_id": payment.transaction_id,
                "description": reason or "Возврат средств"
            }
            
            # Здесь должна быть логика создания возврата в ЮKassa
            # Для примера возвращаем успешный результат
            
            # Создаем запись о возврате в нашей системе
            refund = Refund.objects.create(
                payment=payment,
                amount=refund_amount,
                reason=reason,
                status='pending'
            )
            
            # Обновляем статус платежа
            payment.status = 'refunded'
            payment.save()
            
            logger.info(f"Создан возврат: {refund.id}")
            
            return {
                'success': True,
                'refund_id': refund.id,
                'message': 'Возврат средств инициирован'
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания возврата: {str(e)}")
            return {
                'success': False,
                'error': f"Ошибка создания возврата: {str(e)}"
            }
    
    @staticmethod
    def get_payment_status(transaction_id):
        """Получение статуса платежа из ЮKassa"""
        try:
            yookassa_payment = Payment.find_one(transaction_id)
            return {
                'status': yookassa_payment.status,
                'paid': yookassa_payment.paid,
                'amount': yookassa_payment.amount.value,
                'currency': yookassa_payment.amount.currency,
                'created_at': yookassa_payment.created_at,
                'description': yookassa_payment.description
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса платежа: {str(e)}")
            return {
                'success': False,
                'error': f"Ошибка получения статуса платежа: {str(e)}"
            }
    
    @staticmethod
    def cancel_payment(payment):
        """Отмена платежа"""
        try:
            # В ЮKassa отмена возможна только до подтверждения
            # Здесь должна быть логика отмены в ЮKassa
            
            payment.status = 'cancelled'
            payment.cancelled_at = timezone.now()
            payment.save()
            
            logger.info(f"Платеж отменен: {payment.id}")
            
            return {
                'success': True,
                'message': 'Платеж отменен'
            }
            
        except Exception as e:
            logger.error(f"Ошибка отмены платежа: {str(e)}")
            return {
                'success': False,
                'error': f"Ошибка отмены платежа: {str(e)}"
            }

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def format_amount_for_yookassa(amount):
    """Форматирование суммы для ЮKassa"""
    return f"{amount:.2f}"

def validate_payment_data(student, course, amount):
    """Валидация данных платежа"""
    errors = []
    
    if not student:
        errors.append("Студент обязателен")
    
    if not course:
        errors.append("Курс обязателен")
    
    if amount <= 0:
        errors.append("Сумма должна быть больше 0")
    
    if amount > 100000:  # Ограничение на максимальную сумму
        errors.append("Сумма слишком велика")
    
    return errors

def send_payment_confirmation_email(payment):
    """Отправка email подтверждения оплаты"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        if payment.student.email:
            subject = f"Подтверждение оплаты курса: {payment.course.title}"
            message = f"""
            Здравствуйте, {payment.student.get_full_name() or payment.student.username}!
            
            Спасибо за оплату курса "{payment.course.title}".
            
            Детали платежа:
            - Сумма: {payment.amount} {payment.currency}
            - Дата оплаты: {payment.paid_at.strftime('%d.%m.%Y %H:%M')}
            - Номер платежа: {payment.transaction_id}
            
            Вы успешно зачислены на курс. Доступ к занятиям открыт.
            
            С уважением,
            Онлайн-школа
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [payment.student.email],
                fail_silently=True,
            )
            
            logger.info(f"Отправлено email подтверждения оплаты: {payment.student.email}")
            
    except Exception as e:
        logger.error(f"Ошибка отправки email подтверждения оплаты: {str(e)}")

def send_payment_failure_email(payment, error_message):
    """Отправка email о неудачной оплате"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        if payment.student.email:
            subject = f"Ошибка оплаты курса: {payment.course.title}"
            message = f"""
            Здравствуйте, {payment.student.get_full_name() or payment.student.username}!
            
            К сожалению, произошла ошибка при оплате курса "{payment.course.title}".
            
            Ошибка: {error_message}
            
            Пожалуйста, попробуйте повторить оплату или свяжитесь с поддержкой.
            
            С уважением,
            Онлайн-школа
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [payment.student.email],
                fail_silently=True,
            )
            
            logger.info(f"Отправлено email об ошибке оплаты: {payment.student.email}")
            
    except Exception as e:
        logger.error(f"Ошибка отправки email об ошибке оплаты: {str(e)}")