# admin_panel/permissions.py
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'super_admin']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'super_admin']

class IsSuperAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'super_admin'