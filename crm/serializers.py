from rest_framework import serializers
from .models import StudentProfile, TeacherProfile, Lead, StudentActivity, AnalyticsReport
from accounts.models import User
from courses.models import Course

class StudentProfileSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = '__all__'
        read_only_fields = ['student', 'created_at', 'updated_at']

class TeacherProfileSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    
    class Meta:
        model = TeacherProfile
        fields = '__all__'
        read_only_fields = ['teacher', 'created_at', 'updated_at']

class LeadSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    interested_course_name = serializers.CharField(source='interested_course.title', read_only=True, allow_null=True)
    
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'converted_at']
    
    def validate_email(self, value):
        if Lead.objects.filter(email=value, status__in=['new', 'contacted', 'interested']).exists():
            raise serializers.ValidationError('Лид с таким email уже существует')
        return value

class StudentActivitySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    
    class Meta:
        model = StudentActivity
        fields = '__all__'
        read_only_fields = ['created_at']

class AnalyticsReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = AnalyticsReport
        fields = '__all__'
        read_only_fields = ['generated_at', 'generated_by']

class StudentPerformanceSerializer(serializers.Serializer):
    """Сериализатор для успеваемости студента"""
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    total_lessons = serializers.IntegerField()
    attended_lessons = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    average_rating = serializers.FloatField()
    completed_courses = serializers.IntegerField()
    total_payments = serializers.DecimalField(max_digits=10, decimal_places=2)

class TeacherPerformanceSerializer(serializers.Serializer):
    """Сериализатор для эффективности преподавателя"""
    teacher_id = serializers.IntegerField()
    teacher_name = serializers.CharField()
    total_groups = serializers.IntegerField()
    total_students = serializers.IntegerField()
    average_rating = serializers.FloatField()
    lessons_conducted = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)

class FinancialReportSerializer(serializers.Serializer):
    """Сериализатор для финансового отчета"""
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_payments = serializers.IntegerField()
    average_payment = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_by_course = serializers.DictField()
    revenue_by_month = serializers.DictField()

class LeadReportSerializer(serializers.Serializer):
    """Сериализатор для отчета по лидам"""
    total_leads = serializers.IntegerField()
    leads_by_status = serializers.DictField()
    leads_by_source = serializers.DictField()
    conversion_rate = serializers.FloatField()
    average_conversion_time = serializers.IntegerField()