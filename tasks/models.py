# tasks/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Task(models.Model):
    """Task that users can invest in"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    video = models.FileField(upload_to='tasks/videos/', blank=True, null=True, help_text="Upload a video file (MP4, WebM, etc.)")
    video_url = models.URLField(blank=True, null=True, help_text="Or provide a YouTube/Vimeo URL")
    
    # Bronze tier
    bronze_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bronze_reward = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Silver tier
    silver_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    silver_reward = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Gold tier
    gold_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gold_reward = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    requires_subscription = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class UserTaskInvestment(models.Model):
    """User's investment in a specific task tier"""
    TIER_CHOICES = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('active', 'Active - Countdown Started'),
        ('completed', 'Completed - Ready for Withdrawal'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_investments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='investments')
    tier = models.CharField(max_length=10, choices=TIER_CHOICES)
    
    # Investment details
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reward_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin tracking
    admin_notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_tasks')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timeline
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Set dates when activated
        if self.status == 'active' and not self.start_date:
            self.start_date = timezone.now()
            self.end_date = timezone.now() + timedelta(days=30)  # 30-day countdown
        
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
    def profit(self):
        return self.reward_amount - self.amount
    
    def __str__(self):
        return f"{self.user.email} - {self.task.title} ({self.tier}) - {self.status}"