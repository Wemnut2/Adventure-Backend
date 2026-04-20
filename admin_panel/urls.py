# admin_panel/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminDashboardView, AdminUserManagementViewSet, AdminInvestmentPlanViewSet,
    AdminUserInvestmentViewSet, AdminTaskViewSet, AdminTransactionViewSet,AdminTaskInvestmentViewSet, 
    SystemSettingsViewSet, AdminChallengeViewSet
)
from .views import AdminInvestmentManagementViewSet

router = DefaultRouter()
router.register('users', AdminUserManagementViewSet, basename='admin-user')
router.register('investment-plans', AdminInvestmentPlanViewSet, basename='admin-investment-plan')
router.register('user-investments', AdminUserInvestmentViewSet, basename='admin-user-investment')
router.register('task-investments', AdminTaskInvestmentViewSet, basename='admin-task-investment')
router.register('tasks', AdminTaskViewSet, basename='admin-task')
router.register('transactions', AdminTransactionViewSet, basename='admin-transaction')
router.register('settings', SystemSettingsViewSet, basename='admin-setting')
router.register('challenges', AdminChallengeViewSet, basename='admin-challenge')
router.register('investments', AdminInvestmentManagementViewSet, basename='admin-investment')

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('', include(router.urls)),
]