from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('teacher', 'Преподаватель'),
        ('student', 'Студент'),
        ('parent', 'Родитель'),
    )
    
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES,
        verbose_name=_('Роль пользователя')
    )
    birth_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name=_('Дата рождения')
    )
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name=_('Родитель'),
        limit_choices_to={'role': 'parent'}
    )
    phone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name=_('Номер телефона')
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name=_('Аватар')
    )
    has_studied_language = models.BooleanField(
        default=False,
        verbose_name=_('Ранее изучал язык')
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
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_parent(self):
        return self.role == 'parent'
    
    def get_children(self):
        """Получить детей для родителя"""
        if self.is_parent:
            return self.children.all()
        return []

# === НОВЫЕ МОДЕЛИ ДЛЯ РЕГИСТРАЦИИ И ОПРОСА ===

class RegistrationProfile(models.Model):
    """Дополнительные данные профиля регистрации"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='registration_profile'
    )
    goals = models.TextField(
        blank=True,
        verbose_name=_('Цели изучения языка')
    )
    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Возраст (для детей)')
    )
    learning_goals = models.TextField(
        blank=True,
        verbose_name=_('Цели обучения')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Профиль регистрации'
        verbose_name_plural = 'Профили регистрации'

class SurveyQuestion(models.Model):
    """Вопросы для опроса"""
    QUESTION_TYPE_CHOICES = [
        ('single_choice', 'Один выбор'),
        ('multiple_choice', 'Множественный выбор'),
        ('text', 'Текстовый ответ'),
    ]
    
    question_text = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='single_choice',
        verbose_name='Тип вопроса'
    )
    is_required = models.BooleanField(default=True, verbose_name='Обязательный')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    class Meta:
        verbose_name = 'Вопрос опроса'
        verbose_name_plural = 'Вопросы опроса'
        ordering = ['order']

class SurveyOption(models.Model):
    """Варианты ответов для вопроса"""
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name='options'
    )
    option_text = models.CharField(max_length=255, verbose_name='Текст варианта')
    value = models.CharField(max_length=100, verbose_name='Значение')
    
    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'

class SurveyResponse(models.Model):
    """Ответы пользователя на опрос"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='account_survey_responses'  # Изменили related_name
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE
    )
    selected_options = models.ManyToManyField(
        SurveyOption,
        blank=True,
        verbose_name='Выбранные варианты'
    )
    text_answer = models.TextField(
        blank=True,
        verbose_name='Текстовый ответ'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ответ на опрос'
        verbose_name_plural = 'Ответы на опросы'

class LanguageTest(models.Model):
    """Тест для определения уровня"""
    title = models.CharField(max_length=255, verbose_name='Название теста')
    description = models.TextField(verbose_name='Описание')
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name='Длительность (мин)')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    
    class Meta:
        verbose_name = 'Языковой тест'
        verbose_name_plural = 'Языковые тесты'

from django.db import models

class TestQuestion(models.Model):
    """Вопрос теста"""
    test = models.ForeignKey(
        'LanguageTest',
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField(verbose_name='Текст вопроса')

    # ✅ Новое поле для изображения
    image = models.ImageField(
        upload_to='test_questions/',
        blank=True,
        null=True,
        verbose_name='Изображение к вопросу'
    )

    question_type = models.CharField(
        max_length=20,
        choices=[
            ('single_choice', 'Один выбор'),
            ('multiple_choice', 'Множественный выбор'),
            ('text', 'Текстовый ответ'),
        ],
        default='single_choice'
    )
    correct_answer = models.TextField(verbose_name='Правильный ответ')
    points = models.PositiveIntegerField(default=1, verbose_name='Баллы')

    class Meta:
        verbose_name = 'Вопрос теста'
        verbose_name_plural = 'Вопросы теста'

    def __str__(self):
        return f"Вопрос #{self.pk} ({self.test})"


class TestOption(models.Model):
    """Вариант ответа для вопроса теста"""
    question = models.ForeignKey(
        TestQuestion,
        on_delete=models.CASCADE,
        related_name='options'
    )
    option_text = models.CharField(max_length=255, verbose_name='Текст варианта')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    
    class Meta:
        verbose_name = 'Вариант ответа теста'
        verbose_name_plural = 'Варианты ответов теста'

class TestResult(models.Model):
    """Результат теста пользователя"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='account_test_results'  # Изменили related_name
    )
    test = models.ForeignKey(
        LanguageTest,
        on_delete=models.CASCADE
    )
    score = models.PositiveIntegerField(verbose_name='Баллы')
    total_points = models.PositiveIntegerField(verbose_name='Всего баллов')
    percentage = models.FloatField(verbose_name='Процент')
    level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Начальный'),
            ('elementary', 'Элементарный'),
            ('intermediate', 'Средний'),
            ('upper_intermediate', 'Выше среднего'),
            ('advanced', 'Продвинутый'),
            ('proficient', 'Владение на уровне носителя'),
        ],
        verbose_name='Уровень'
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'

class ConsultationRequest(models.Model):
    """Запрос на консультацию"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='consultation_requests'
    )
    name = models.CharField(max_length=255, verbose_name='Имя')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    language_level = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Уровень языка'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Сообщение'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('new', 'Новый'),
            ('in_progress', 'В работе'),
            ('completed', 'Завершен'),
        ],
        default='new',
        verbose_name='Статус'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    contacted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Запрос консультации'
        verbose_name_plural = 'Запросы консультаций'
        ordering = ['-requested_at']