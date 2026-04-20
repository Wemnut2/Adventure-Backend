# admin_panel/admin.py
from django.contrib import admin
from .models import AdminAction, SystemSettings

class AdminActionAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action_type', 'target_user', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('admin__email', 'target_user__email', 'details')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Actions are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Cannot change actions

class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        ('Setting', {
            'fields': ('key', 'value', 'description')
        }),
        ('Metadata', {
            'fields': ('updated_at',)
        }),
    )

# Register models
admin.site.register(AdminAction, AdminActionAdmin)
admin.site.register(SystemSettings, SystemSettingsAdmin)