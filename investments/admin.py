# investments/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import InvestmentPlan, UserInvestment, InvestmentTransaction


class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_amount', 'max_amount', 'expected_return', 'duration_days', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'expected_return', 'duration_days')
    fieldsets = (
        ('Plan Information', {
            'fields': ('name', 'description')
        }),
        ('Financial Settings', {
            'fields': ('min_amount', 'max_amount', 'expected_return', 'duration_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


class UserInvestmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'amount', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('user__email', 'user__username', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'expected_return_amount', 'daily_profit')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('User & Plan', {
            'fields': ('user', 'plan', 'amount', 'status')
        }),
        ('Admin Verification', {
            'fields': ('admin_notes', 'verified_by', 'verified_at')
        }),
        ('Returns', {
            'fields': ('expected_return_amount', 'daily_profit', 'total_profit')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'completed_date', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['verify_investments', 'complete_investments']
    
    def verify_investments(self, request, queryset):
        from django.utils import timezone
        for inv in queryset.filter(status='pending'):
            inv.status = 'active'
            inv.verified_by = request.user
            inv.verified_at = timezone.now()
            inv.start_date = timezone.now()
            inv.end_date = timezone.now() + timezone.timedelta(days=inv.plan.duration_days)
            inv.save()
        self.message_user(request, f'{queryset.count()} investments verified and countdown started.')
    verify_investments.short_description = "Verify selected investments & start countdown"
    
    def complete_investments(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='active').update(status='completed', completed_date=timezone.now())
        self.message_user(request, f'{updated} investments completed.')
    complete_investments.short_description = "Complete selected investments"


class InvestmentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_investment', 'transaction_type', 'amount', 'reference', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user_investment__user__email', 'reference')
    readonly_fields = ('created_at',)


# Register models
admin.site.register(InvestmentPlan, InvestmentPlanAdmin)
admin.site.register(UserInvestment, UserInvestmentAdmin)
admin.site.register(InvestmentTransaction, InvestmentTransactionAdmin)