# investments/models.py - Simplified version without verified_by
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

class InvestmentPlan(models.Model):
    """Investment plans that users can invest in"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_return = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    duration_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.expected_return}% return"


class UserInvestment(models.Model):
    """User's investment record"""
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('active', 'Active - Countdown Started'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin tracking
    admin_notes = models.TextField(blank=True, null=True)
    
    # Timeline
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Returns
    expected_return_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    daily_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def save(self, *args, **kwargs):
        if self.amount and self.plan:
            self.expected_return_amount = self.amount + (self.amount * self.plan.expected_return / 100)
            self.daily_profit = (self.amount * self.plan.expected_return / 100) / self.plan.duration_days
        
        if self.status == 'active' and not self.start_date:
            self.start_date = timezone.now()
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        
        super().save(*args, **kwargs)
    
    @property
    def days_remaining(self):
        if self.end_date and self.status == 'active':
            remaining = (self.end_date - timezone.now()).days
            return max(0, remaining)
        return 0
    
    @property
    def progress_percentage(self):
        if self.start_date and self.end_date and self.status == 'active':
            total = (self.end_date - self.start_date).days
            elapsed = (timezone.now() - self.start_date).days
            if total > 0:
                return min(100, max(0, int((elapsed / total) * 100)))
        return 0
    
    @property
    def plan_name(self):
        return self.plan.name
    
    @property
    def plan_description(self):
        return self.plan.description
    
    @property
    def user_email(self):
        return self.user.email
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - {self.status}"


class InvestmentTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('investment', 'Investment'),
        ('profit', 'Profit Credit'),
        ('withdrawal', 'Withdrawal'),
    )
    
    user_investment = models.ForeignKey(UserInvestment, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} - ${self.amount}"
# Alias for backward compatibility
Investment = UserInvestment
Transaction = InvestmentTransaction