# tasks/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, UserTaskInvestmentViewSet

router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')
router.register('investments', UserTaskInvestmentViewSet, basename='task-investment')

urlpatterns = [
    path('', include(router.urls)),
]