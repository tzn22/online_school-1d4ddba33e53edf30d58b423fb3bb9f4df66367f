from django.utils import timezone
from .models import Feedback, FeedbackResponse, Survey, SurveyResponse
from django.db import models

class FeedbackService:
    """Сервис для работы с обратной связью"""
    
    @staticmethod
    def create_feedback(student, lesson=None, teacher=None, course=None, 
                       feedback_type='lesson', title='', content='', 
                       rating=None, is_anonymous=False):
        """Создание обратной связи"""
        feedback = Feedback.objects.create(
            student=student,
            lesson=lesson,
            teacher=teacher,
            course=course,
            feedback_type=feedback_type,
            title=title,
            content=content,
            rating=rating,
            is_anonymous=is_anonymous
        )
        return feedback
    
    @staticmethod
    def respond_to_feedback(feedback, responder, content, is_internal=False):
        """Ответ на обратную связь"""
        response = FeedbackResponse.objects.create(
            feedback=feedback,
            responder=responder,
            content=content,
            is_internal=is_internal
        )
        
        # Обновляем статус обратной связи
        if not is_internal:
            feedback.status = 'in_progress'
            feedback.save()
        
        return response
    
    @staticmethod
    def resolve_feedback(feedback, resolver):
        """Решение обратной связи"""
        feedback.status = 'resolved'
        feedback.resolved_at = timezone.now()
        feedback.save()
        return feedback
    
    @staticmethod
    def get_student_feedback_stats(student):
        """Получение статистики отзывов студента"""
        total_feedback = Feedback.objects.filter(student=student).count()
        avg_rating = Feedback.objects.filter(
            student=student, 
            rating__isnull=False
        ).aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating']
        
        return {
            'total_feedback': total_feedback,
            'average_rating': float(avg_rating) if avg_rating else 0
        }
    
    @staticmethod
    def get_teacher_feedback_stats(teacher):
        """Получение статистики отзывов преподавателя"""
        total_feedback = Feedback.objects.filter(teacher=teacher).count()
        avg_rating = Feedback.objects.filter(
            teacher=teacher, 
            rating__isnull=False
        ).aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating']
        
        # Распределение оценок
        rating_distribution = Feedback.objects.filter(
            teacher=teacher,
            rating__isnull=False
        ).values('rating').annotate(
            count=models.Count('rating')
        ).order_by('rating')
        
        return {
            'total_feedback': total_feedback,
            'average_rating': float(avg_rating) if avg_rating else 0,
            'rating_distribution': list(rating_distribution)
        }

class SurveyService:
    """Сервис для работы с опросами"""
    
    @staticmethod
    def submit_survey_response(survey, respondent, answers):
        """Отправка ответов на опрос"""
        # Проверяем, что опрос активен
        if survey.status != 'active':
            raise Exception('Опрос не активен')
        
        # Проверяем даты
        now = timezone.now()
        if survey.start_date and now < survey.start_date:
            raise Exception('Опрос еще не начался')
        if survey.end_date and now > survey.end_date:
            raise Exception('Опрос уже завершен')
        
        # Создаем или обновляем ответ
        response, created = SurveyResponse.objects.update_or_create(
            survey=survey,
            respondent=respondent,
            defaults={
                'answers': answers,
                'submitted_at': timezone.now()
            }
        )
        
        return response
    
    @staticmethod
    def get_survey_statistics(survey):
        """Получение статистики опроса"""
        total_responses = SurveyResponse.objects.filter(survey=survey).count()
        
        # Получаем все вопросы опроса
        questions = survey.questions.all()
        question_stats = []
        
        for question in questions:
            if question.question_type in ['single_choice', 'multiple_choice']:
                # Статистика для выбора
                answers = SurveyResponse.objects.filter(survey=survey).values_list('answers', flat=True)
                option_counts = {}
                
                for answer_dict in answers:
                    if str(question.id) in answer_dict:
                        selected_options = answer_dict[str(question.id)]
                        if isinstance(selected_options, list):
                            for option in selected_options:
                                option_counts[option] = option_counts.get(option, 0) + 1
                        else:
                            option_counts[selected_options] = option_counts.get(selected_options, 0) + 1
                
                question_stats.append({
                    'question': question.question_text,
                    'type': question.question_type,
                    'options': option_counts
                })
            elif question.question_type == 'rating':
                # Статистика для оценок
                answers = SurveyResponse.objects.filter(survey=survey).values_list('answers', flat=True)
                ratings = []
                
                for answer_dict in answers:
                    if str(question.id) in answer_dict:
                        try:
                            rating = int(answer_dict[str(question.id)])
                            ratings.append(rating)
                        except (ValueError, TypeError):
                            pass
                
                if ratings:
                    avg_rating = sum(ratings) / len(ratings)
                    question_stats.append({
                        'question': question.question_text,
                        'type': question.question_type,
                        'average_rating': avg_rating,
                        'total_ratings': len(ratings)
                    })
        
        return {
            'total_responses': total_responses,
            'question_statistics': question_stats
        }