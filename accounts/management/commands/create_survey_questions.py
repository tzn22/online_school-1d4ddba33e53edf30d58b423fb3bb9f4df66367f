# Создай папки: accounts/management/commands/
# accounts/management/__init__.py (пустой файл)
# accounts/management/commands/__init__.py (пустой файл)

from django.core.management.base import BaseCommand
from accounts.models import SurveyQuestion, SurveyOption

class Command(BaseCommand):
    help = 'Создать тестовые вопросы опроса'
    
    def handle(self, *args, **options):
        # Создаем вопросы опроса
        questions_data = [
            {
                'question_text': 'Какова ваша основная цель изучения языка?',
                'question_type': 'multiple_choice',
                'is_required': True,
                'order': 1,
                'options': [
                    {'option_text': 'Бизнес и карьера', 'value': 'business'},
                    {'option_text': 'Путешествия', 'value': 'travel'},
                    {'option_text': 'Общение с носителями языка', 'value': 'communication'},
                    {'option_text': 'Академические цели', 'value': 'academic'},
                    {'option_text': 'Переезд в другую страну', 'value': 'relocation'},
                ]
            },
            {
                'question_text': 'Сколько времени в неделю вы можете уделять занятиям?',
                'question_type': 'single_choice',
                'is_required': True,
                'order': 2,
                'options': [
                    {'option_text': '1-2 часа', 'value': '1-2'},
                    {'option_text': '3-5 часов', 'value': '3-5'},
                    {'option_text': '6-10 часов', 'value': '6-10'},
                    {'option_text': 'Более 10 часов', 'value': '10+'},
                ]
            },
            {
                'question_text': 'Какой формат занятий вам больше подходит?',
                'question_type': 'multiple_choice',
                'is_required': True,
                'order': 3,
                'options': [
                    {'option_text': 'Индивидуальные занятия', 'value': 'individual'},
                    {'option_text': 'Групповые занятия', 'value': 'group'},
                    {'option_text': 'Онлайн', 'value': 'online'},
                    {'option_text': 'Офлайн', 'value': 'offline'},
                ]
            },
            {
                'question_text': 'Какие методы обучения вам больше нравятся?',
                'question_type': 'multiple_choice',
                'is_required': False,
                'order': 4,
                'options': [
                    {'option_text': 'Игровые методы', 'value': 'games'},
                    {'option_text': 'Практические задания', 'value': 'practice'},
                    {'option_text': 'Теоретические материалы', 'value': 'theory'},
                    {'option_text': 'Аудирование', 'value': 'listening'},
                    {'option_text': 'Разговорная практика', 'value': 'speaking'},
                ]
            },
            {
                'question_text': 'Есть ли у вас какие-либо особые потребности в обучении?',
                'question_type': 'text',
                'is_required': False,
                'order': 5,
                'options': []
            }
        ]
        
        # Создаем тестовый языковой тест
        from accounts.models import LanguageTest, TestQuestion, TestOption
        
        # Создаем тест
        test, created = LanguageTest.objects.get_or_create(
            title='Начальный тест по английскому языку',
            description='Тест для определения вашего уровня знаний английского языка',
            duration_minutes=30,
            is_active=True
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Создан тест: {test.title}')
            )
        
        # Создаем вопросы для теста
        test_questions = [
            {
                'question_text': 'Выберите правильный вариант: I ___ to school every day.',
                'question_type': 'single_choice',
                'correct_answer': 'go',
                'points': 1,
                'options': [
                    {'option_text': 'goes', 'is_correct': False},
                    {'option_text': 'go', 'is_correct': True},
                    {'option_text': 'going', 'is_correct': False},
                    {'option_text': 'went', 'is_correct': False},
                ]
            },
            {
                'question_text': 'Как переводится слово "book"?',
                'question_type': 'single_choice',
                'correct_answer': 'книга',
                'points': 1,
                'options': [
                    {'option_text': 'машина', 'is_correct': False},
                    {'option_text': 'книга', 'is_correct': True},
                    {'option_text': 'телефон', 'is_correct': False},
                    {'option_text': 'дом', 'is_correct': False},
                ]
            },
            {
                'question_text': 'Составьте предложение: she / like / apples',
                'question_type': 'text',
                'correct_answer': 'She likes apples.',
                'points': 2,
                'options': []
            }
        ]
        
        # Создаем вопросы теста
        for i, q_data in enumerate(test_questions, 1):
            question, created = TestQuestion.objects.get_or_create(
                test=test,
                question_text=q_data['question_text'],
                defaults={
                    'question_type': q_data['question_type'],
                    'correct_answer': q_data['correct_answer'],
                    'points': q_data['points']
                }
            )
            
            if created:
                # Создаем варианты ответов
                for opt_data in q_data['options']:
                    TestOption.objects.create(
                        question=question,
                        option_text=opt_data['option_text'],
                        is_correct=opt_data['is_correct']
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Создан вопрос теста: {question.question_text}')
                )
        
        # Создаем вопросы опроса
        for q_data in questions_data:
            question, created = SurveyQuestion.objects.get_or_create(
                question_text=q_data['question_text'],
                defaults={
                    'question_type': q_data['question_type'],
                    'is_required': q_data['is_required'],
                    'order': q_data['order']
                }
            )
            
            if created:
                # Создаем варианты ответов
                for opt_data in q_data['options']:
                    SurveyOption.objects.create(
                        question=question,
                        option_text=opt_data['option_text'],
                        value=opt_data['value']
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Создан вопрос опроса: {question.question_text}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Все тестовые данные успешно созданы!')
        )