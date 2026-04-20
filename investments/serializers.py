# investments/serializers.py
from rest_framework import serializers
from .models import InvestmentPlan, UserInvestment, InvestmentTransaction


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
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class InvestmentTransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user_investment.user.email', default='')
    investment_plan = serializers.ReadOnlyField(source='user_investment.plan.name', default='')
    
    class Meta:
        model = InvestmentTransaction
        fields = '__all__'