# admin_panel/serializers.py
from rest_framework import serializers
from accounts.models import User, UserProfile, ActivityLog
from investments.models import InvestmentPlan, UserInvestment, InvestmentTransaction
from tasks.models import Task, UserTaskInvestment
from .models import AdminAction, SystemSettings

class UserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'is_subscribed', 
                  'phone_number', 'created_at', 'subscription_end_date', 'is_active', 'plain_password']


class UserProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = UserProfile
        fields = '__all__'


class InvestmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentPlan
        fields = '__all__'


class UserInvestmentSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='plan.name')
    plan_description = serializers.ReadOnlyField(source='plan.description')
    user_email = serializers.ReadOnlyField(source='user.email')
    days_remaining = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = UserInvestment
        fields = [
            'id', 'user', 'user_email', 'plan', 'plan_name', 'plan_description',
            'amount', 'status', 'admin_notes', 'start_date', 'end_date', 
            'completed_date', 'created_at', 'updated_at', 'expected_return_amount',
            'daily_profit', 'total_profit', 'days_remaining', 'progress_percentage'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'expected_return_amount', 'daily_profit']


class InvestmentTransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user_investment.user.email', default='')
    investment_plan = serializers.ReadOnlyField(source='user_investment.plan.name', default='')
    
    class Meta:
        model = InvestmentTransaction
        fields = '__all__'


class TaskManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'



class UserTaskInvestmentSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    task_title = serializers.ReadOnlyField(source='task.title')
    task_description = serializers.ReadOnlyField(source='task.description')
    days_remaining = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    profit = serializers.ReadOnlyField()
    
    class Meta:
        model = UserTaskInvestment
        fields = [
            'id', 'user', 'user_email', 'task', 'task_title', 'task_description',
            'tier', 'amount', 'reward_amount', 'status', 'admin_notes',
            'start_date', 'end_date', 'completed_date', 'created_at', 'updated_at',
            'days_remaining', 'progress_percentage', 'profit'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class AdminActionSerializer(serializers.ModelSerializer):
    admin_email = serializers.ReadOnlyField(source='admin.email')
    target_user_email = serializers.ReadOnlyField(source='target_user.email')
    
    class Meta:
        model = AdminAction
        fields = '__all__'


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = '__all__'


class ChallengeParticipantSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'user_username', 'full_name', 'gender', 'age',
            'monthly_income', 'marital_status', 'contact_number', 'hearing_status',
            'housing_situation', 'preferred_payment_method', 'location', 'challenge_status',
            'registration_fee_paid', 'insurance_fee_paid', 'total_prize',
            'challenge_start_date', 'challenge_end_date', 'participant_signature',
            'participant_signature_date', 'ceo_signature', 'ceo_signature_date',
            'challenge_completed_date', 'challenge_reward_claimed', 'admin_notes'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    subscribed_users = serializers.IntegerField()
    active_investments = serializers.IntegerField()
    total_volume = serializers.DecimalField(max_digits=12, decimal_places=2)
    completed_tasks = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    challenge_participants = serializers.IntegerField()
    recent_users = UserManagementSerializer(many=True, read_only=True)
    recent_activities = serializers.ListField(child=serializers.DictField(), read_only=True)