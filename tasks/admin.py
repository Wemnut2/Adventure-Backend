# tasks/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Task, UserTaskInvestment  # Changed from UserTask
from investments.models import Transaction
import uuid


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'bronze_price', 'silver_price', 'gold_price', 'is_active', 'video_preview')
    list_editable = ('bronze_price', 'silver_price', 'gold_price', 'is_active')
    search_fields = ('title',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'video')
        }),
        ('Pricing', {
            'fields': ('bronze_price', 'silver_price', 'gold_price')
        }),
        ('Rewards', {
            'fields': ('bronze_reward', 'silver_reward', 'gold_reward')
        }),
        ('Settings', {
            'fields': ('requires_subscription', 'is_active')
        }),
    )

    def video_preview(self, obj):
        if obj.video:
            return format_html(
                '<video width="120" height="70" controls>'
                '<source src="{}" type="video/mp4">'
                '</video>',
                obj.video.url
            )
        return '—'
    video_preview.short_description = 'Preview'


@admin.register(UserTaskInvestment)  # Changed from UserTask
class UserTaskInvestmentAdmin(admin.ModelAdmin):  # Changed class name
    list_display = (
        'user', 'task', 'tier', 'status',
        'amount', 'reward_amount',
        'start_date', 'end_date', 'completed_date'
    )
    list_filter = ('status', 'tier', 'task')
    search_fields = ('user__email', 'task__title')
    ordering = ('-created_at',)
    readonly_fields = ('start_date', 'end_date', 'completed_date', 'created_at', 'updated_at')

    actions = ['verify_investments', 'mark_completed', 'reject_investments']

    def verify_investments(self, request, queryset):
        """Verify pending task investments"""
        updated = 0
        for investment in queryset.filter(status='pending'):
            investment.status = 'active'
            investment.start_date = timezone.now()
            investment.end_date = timezone.now() + timezone.timedelta(days=30)
            investment.verified_by = request.user
            investment.verified_at = timezone.now()
            investment.save()
            updated += 1
        
        self.message_user(request, f"{updated} task investment(s) verified and activated.")
    verify_investments.short_description = 'Verify selected task investments'

    def mark_completed(self, request, queryset):
        """Mark active investments as completed"""
        updated = 0
        for investment in queryset.filter(status='active'):
            investment.status = 'completed'
            investment.completed_date = timezone.now()
            investment.save()
            updated += 1
        
        self.message_user(request, f"{updated} task investment(s) marked as completed.")
    mark_completed.short_description = 'Mark selected as completed'

    def reject_investments(self, request, queryset):
        """Reject pending investments"""
        updated = queryset.filter(status='pending').update(status='cancelled')
        self.message_user(request, f"{updated} task investment(s) rejected.")
    reject_investments.short_description = 'Reject selected task investments'