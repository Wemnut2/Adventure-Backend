# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import User, UserProfile, ActivityLog

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'plain_password', 'role', 'is_subscribed', 'is_active', 'created_at')
    list_filter = ('role', 'is_subscribed', 'is_active')
    search_fields = ('email', 'username', 'plain_password', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Testing Only - Plain Password', {'fields': ('plain_password',)}),
        ('Personal Info', {'fields': ('phone_number', 'address')}),
        ('Account Information', {'fields': ('bank_name', 'account_number', 'account_name', 
                                           'btc_wallet', 'eth_wallet', 'usdt_wallet')}),
        ('Subscription', {'fields': ('is_subscribed', 'subscription_start_date', 'subscription_end_date')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 
                                   'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'challenge_status', 'registration_fee_paid', 'insurance_fee_paid')
    list_filter = ('challenge_status', 'registration_fee_paid', 'insurance_fee_paid', 'gender', 'marital_status')
    search_fields = ('user__email', 'user__username', 'full_name', 'contact_number')
    readonly_fields = ('participant_signature_date', 'ceo_signature_date', 'challenge_completed_date')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'profile_picture')
        }),
        ('Personal Details', {
            'fields': ('gender', 'age', 'date_of_birth', 'marital_status', 
                      'contact_number', 'location')  # Removed 'address' - it belongs to User model
        }),
        ('Financial Information', {
            'fields': ('monthly_income', 'preferred_payment_method')
        }),
        ('Challenge Information', {
            'fields': ('challenge_status', 'challenge_start_date', 'challenge_end_date',
                      'total_prize', 'registration_fee_paid', 'insurance_fee_paid',
                      'registration_fee_amount', 'insurance_fee_amount')
        }),
        ('Medical Information', {
            'fields': ('hearing_status', 'housing_situation')
        }),
        ('Signatures', {
            'fields': ('participant_signature', 'participant_signature_date',
                      'ceo_signature', 'ceo_signature_date')
        }),
        ('Completion & Admin', {
            'fields': ('challenge_completed_date', 'challenge_reward_claimed', 'admin_notes')
        }),
    )

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'action')
    readonly_fields = ('created_at',)

# Register models
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)